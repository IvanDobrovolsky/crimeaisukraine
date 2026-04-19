#!/usr/bin/env python3
"""
Look up SJR quartiles for all journals in the CrossRef-enriched dataset
using the OpenAlex sources API (which includes SJR-derived metrics).

OpenAlex sources endpoint returns:
  - type (journal, repository, conference, ebook platform, etc.)
  - is_in_doaj (DOAJ = reputable open access)
  - summary_stats.2yr_mean_citedness (proxy for impact factor)
  - summary_stats.h_index
  - works_count, cited_by_count

We classify Q1/Q2/Q3/Q4 based on 2yr_mean_citedness relative to field norms.

Usage:
    python3 pipelines/academic/scimago_lookup.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent.parent
INPUT = ROOT / "data" / "academic_russia_crossref.jsonl"
OUTPUT = ROOT / "data" / "academic_russia_enriched.jsonl"
CACHE_FILE = ROOT / "data" / "openalex_sources_cache.json"

CONTACT = "dobrovolsky94@gmail.com"


def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def lookup_openalex_source(issn):
    """Look up journal by ISSN in OpenAlex sources API."""
    url = f"https://api.openalex.org/sources?filter=issn:{issn}&mailto={CONTACT}"
    req = urllib.request.Request(url, headers={
        "User-Agent": f"CrimeaAudit/2.0 (mailto:{CONTACT})"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            results = data.get("results", [])
            if not results:
                return None
            src = results[0]
            stats = src.get("summary_stats", {})
            return {
                "openalex_id": src.get("id", ""),
                "display_name": src.get("display_name", ""),
                "type": src.get("type", ""),
                "is_in_doaj": src.get("is_in_doaj", False),
                "works_count": src.get("works_count", 0),
                "cited_by_count": src.get("cited_by_count", 0),
                "h_index": stats.get("h_index", 0),
                "2yr_mean_citedness": stats.get("2yr_mean_citedness", 0),
                "i10_index": stats.get("i10_index", 0),
            }
    except Exception as e:
        return {"error": str(e)[:100]}


def lookup_scimago_api(issn):
    """Try Scimago's search page to get quartile info."""
    url = f"https://www.scimagojr.com/journalsearch.php?q={issn}&tip=iss"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode(errors="replace")
            # Look for quartile info in the response
            # Scimago shows journal cards with quartile badges
            import re
            # Find the journal page link
            match = re.search(r'href="journalsearch\.php\?q=(\d+)&amp;tip=sid', html)
            if match:
                sid = match.group(1)
                # Now fetch the journal page
                jurl = f"https://www.scimagojr.com/journalsearch.php?q={sid}&tip=sid"
                jreq = urllib.request.Request(jurl, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                })
                with urllib.request.urlopen(jreq, timeout=15) as jresp:
                    jhtml = jresp.read().decode(errors="replace")
                    # Look for quartile
                    q_match = re.search(r'<span[^>]*class="[^"]*quartile[^"]*"[^>]*>(Q[1-4])</span>', jhtml)
                    if q_match:
                        return {"quartile": q_match.group(1), "scimago_id": sid}
                    # Try alternate pattern
                    q_match2 = re.search(r'Best Quartile\s*</span>\s*<span[^>]*>(Q[1-4])</span>', jhtml)
                    if q_match2:
                        return {"quartile": q_match2.group(1), "scimago_id": sid}
            return None
    except Exception as e:
        return {"error": str(e)[:100]}


def main():
    # Load all papers
    papers = []
    with open(INPUT) as f:
        for line in f:
            papers.append(json.loads(line))
    print(f"Loaded {len(papers)} CrossRef-enriched papers")

    # Collect unique ISSNs
    issn_to_journals = {}
    for p in papers:
        for issn in p.get("issn", []):
            if issn not in issn_to_journals:
                issn_to_journals[issn] = {
                    "journal": p.get("journal_crossref", ""),
                    "publisher": p.get("publisher_crossref", ""),
                    "count": 0
                }
            issn_to_journals[issn]["count"] += 1

    print(f"Unique ISSNs: {len(issn_to_journals)}")

    # Load/build cache
    cache = load_cache()
    to_lookup = [issn for issn in issn_to_journals if issn not in cache]
    print(f"To look up: {len(to_lookup)} ({len(cache)} cached)")

    # OpenAlex source lookups
    for i, issn in enumerate(to_lookup):
        result = lookup_openalex_source(issn)
        if result:
            cache[issn] = result
        else:
            cache[issn] = {"error": "not_found"}

        if (i + 1) % 50 == 0:
            save_cache(cache)
            print(f"  [{i+1}/{len(to_lookup)}] OpenAlex lookups done")

        time.sleep(0.1)  # polite rate

    save_cache(cache)
    print(f"OpenAlex lookups complete. Cache: {len(cache)} entries")

    # Now try Scimago for journals that have decent metrics
    # Only bother for journals with h_index > 5 or 2yr_mean_citedness > 0.5
    scimago_candidates = []
    for issn, info in cache.items():
        if isinstance(info, dict) and not info.get("error"):
            h = info.get("h_index", 0)
            citedness = info.get("2yr_mean_citedness", 0)
            if h > 5 or citedness > 0.3:
                if "scimago" not in info:  # not yet looked up
                    scimago_candidates.append(issn)

    print(f"\nScimago lookups for {len(scimago_candidates)} journals with decent metrics")
    for i, issn in enumerate(scimago_candidates):
        result = lookup_scimago_api(issn)
        if result and not result.get("error"):
            cache[issn]["scimago"] = result
        if (i + 1) % 20 == 0:
            save_cache(cache)
            print(f"  [{i+1}/{len(scimago_candidates)}] Scimago lookups")
        time.sleep(1.0)  # be very polite to Scimago

    save_cache(cache)

    # Enrich papers and write output
    outf = open(OUTPUT, "w")
    stats = Counter()

    for p in papers:
        issns = p.get("issn", [])
        best_source = None
        for issn in issns:
            src = cache.get(issn)
            if src and not src.get("error"):
                if not best_source or src.get("h_index", 0) > best_source.get("h_index", 0):
                    best_source = src

        if best_source:
            p["journal_type"] = best_source.get("type", "")
            p["h_index"] = best_source.get("h_index", 0)
            p["2yr_mean_citedness"] = best_source.get("2yr_mean_citedness", 0)
            p["is_in_doaj"] = best_source.get("is_in_doaj", False)
            p["cited_by_count_journal"] = best_source.get("cited_by_count", 0)
            scimago = best_source.get("scimago", {})
            if scimago and scimago.get("quartile"):
                p["sjr_quartile"] = scimago["quartile"]
            else:
                p["sjr_quartile"] = ""
        else:
            p["journal_type"] = ""
            p["h_index"] = 0
            p["2yr_mean_citedness"] = 0
            p["is_in_doaj"] = False
            p["cited_by_count_journal"] = 0
            p["sjr_quartile"] = ""

        pub = p.get("publisher_crossref", "")
        q = p.get("sjr_quartile", "")
        if q:
            stats[f"{q} ({pub[:30]})"] += 1
        else:
            stats[f"no_quartile ({pub[:30]})"] += 1

        outf.write(json.dumps(p, ensure_ascii=False) + "\n")

    outf.close()

    print(f"\n{'='*60}")
    print(f"ENRICHMENT COMPLETE → {OUTPUT}")
    print(f"\nJournals with SJR quartile:")
    for k, v in sorted(stats.items()):
        if not k.startswith("no_quartile"):
            print(f"  {v:3d}  {k}")

    print(f"\nTop journals by h-index (from OpenAlex):")
    seen = set()
    journal_metrics = []
    for issn, info in cache.items():
        if isinstance(info, dict) and not info.get("error"):
            name = info.get("display_name", "")
            if name and name not in seen:
                seen.add(name)
                journal_metrics.append({
                    "name": name,
                    "h_index": info.get("h_index", 0),
                    "2yr_citedness": info.get("2yr_mean_citedness", 0),
                    "type": info.get("type", ""),
                    "issn": issn,
                    "scimago_q": info.get("scimago", {}).get("quartile", ""),
                })
    for j in sorted(journal_metrics, key=lambda x: -x["h_index"])[:40]:
        q_str = f" [{j['scimago_q']}]" if j["scimago_q"] else ""
        print(f"  h={j['h_index']:4d} | cite={j['2yr_citedness']:.2f} | {j['type']:10s} | {j['name'][:60]}{q_str}")


if __name__ == "__main__":
    main()
