#!/usr/bin/env python3
"""
Enrich Russia-confirmed academic papers with real publisher data from CrossRef.

Replaces the broken LLM-guessed journal tiers with ground truth:
  - CrossRef API → real publisher name from DOI prefix
  - ISSN extraction for downstream Scimago lookup

Usage:
    python3 pipelines/academic/crossref_enrich.py
"""

import csv
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_CSV = ROOT / "data" / "academic_russia_confirmed.csv"
OUTPUT_JSONL = ROOT / "data" / "academic_russia_crossref.jsonl"

CROSSREF_API = "https://api.crossref.org/works"
CONTACT = "dobrovolsky94@gmail.com"

# Known DOI prefix → publisher (fallback for CrossRef failures)
PREFIX_PUBLISHERS = {
    "10.1093": "Oxford University Press",
    "10.1016": "Elsevier",
    "10.1002": "Wiley",
    "10.1007": "Springer Nature",
    "10.1134": "Pleiades Publishing (Springer)",
    "10.1080": "Taylor & Francis",
    "10.4324": "Routledge (Taylor & Francis)",
    "10.3390": "MDPI",
    "10.1088": "IOP Publishing",
    "10.1051": "EDP Sciences",
    "10.1109": "IEEE",
    "10.5281": "Zenodo (CERN)",
    "10.2139": "SSRN (Elsevier)",
    "10.1017": "Cambridge University Press",
    "10.1515": "De Gruyter",
    "10.15405": "Future Academy",
    "10.3389": "Frontiers",
    "10.1177": "SAGE Publications",
    "10.1097": "Wolters Kluwer",
}


def get_doi_suffix(doi_url):
    """Extract DOI from full URL."""
    if doi_url.startswith("https://doi.org/"):
        return doi_url[len("https://doi.org/"):]
    if doi_url.startswith("http://doi.org/"):
        return doi_url[len("http://doi.org/"):]
    if doi_url.startswith("10."):
        return doi_url
    return None


def get_prefix(doi):
    """Extract publisher prefix from DOI."""
    parts = doi.split("/")
    if parts:
        return parts[0]
    return None


def lookup_crossref(doi):
    """Fetch metadata from CrossRef for a single DOI."""
    encoded = urllib.parse.quote(doi, safe="/()")
    url = f"{CROSSREF_API}/{encoded}?mailto={CONTACT}"
    req = urllib.request.Request(url, headers={
        "User-Agent": f"CrimeaAudit/2.0 (mailto:{CONTACT})"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            msg = data.get("message", {})
            return {
                "publisher": msg.get("publisher", ""),
                "container_title": (msg.get("container-title") or [""])[0],
                "issn": msg.get("ISSN", []),
                "type": msg.get("type", ""),
                "subject": msg.get("subject", []),
                "member": msg.get("member", ""),
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"publisher": "", "error": "not_in_crossref"}
        return {"publisher": "", "error": f"http_{e.code}"}
    except Exception as e:
        return {"publisher": "", "error": str(e)[:100]}


def main():
    # Load input
    papers = []
    with open(INPUT_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            papers.append(row)
    print(f"Loaded {len(papers)} Russia-confirmed papers")

    # Resume support
    done = set()
    if OUTPUT_JSONL.exists():
        with open(OUTPUT_JSONL, "r") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    done.add(r.get("doi", ""))
                except:
                    pass
        print(f"Already processed: {len(done)}")

    # Filter to papers with DOIs
    to_process = []
    no_doi = []
    for p in papers:
        doi_url = p.get("doi", "").strip()
        doi = get_doi_suffix(doi_url) if doi_url else None
        if doi and doi_url not in done:
            to_process.append((p, doi, doi_url))
        elif not doi:
            no_doi.append(p)

    print(f"To process: {len(to_process)} (skipping {len(no_doi)} without DOI)")

    # Process
    stats = Counter()
    outf = open(OUTPUT_JSONL, "a")
    batch_start = time.time()

    for i, (paper, doi, doi_url) in enumerate(to_process):
        prefix = get_prefix(doi)
        cr = lookup_crossref(doi)

        publisher = cr.get("publisher", "")
        if not publisher and prefix in PREFIX_PUBLISHERS:
            publisher = PREFIX_PUBLISHERS[prefix]

        result = {
            "doi": doi_url,
            "openalex_id": paper.get("openalex_id", ""),
            "title": paper.get("title", ""),
            "year": paper.get("year", ""),
            "journal_openalex": paper.get("journal", ""),
            "journal_crossref": cr.get("container_title", ""),
            "publisher_crossref": publisher,
            "doi_prefix": prefix,
            "issn": cr.get("issn", []),
            "type": cr.get("type", ""),
            "subject": cr.get("subject", []),
            "signals": paper.get("signals", ""),
        }
        if cr.get("error"):
            result["crossref_error"] = cr["error"]

        outf.write(json.dumps(result, ensure_ascii=False) + "\n")
        outf.flush()

        if publisher:
            stats[publisher] += 1
        else:
            stats["(no publisher)"] += 1

        if (i + 1) % 50 == 0:
            elapsed = time.time() - batch_start
            rate = (i + 1) / elapsed
            remaining = (len(to_process) - i - 1) / rate if rate > 0 else 0
            print(f"  [{i+1}/{len(to_process)}] {rate:.1f}/s, ~{remaining:.0f}s left | last: {publisher[:40]}")

        # Polite rate: ~20/sec
        time.sleep(0.05)

    outf.close()

    print(f"\n{'='*60}")
    print(f"CROSSREF ENRICHMENT COMPLETE")
    print(f"  Processed: {len(to_process)}")
    print(f"  No DOI (skipped): {len(no_doi)}")
    print(f"\nTop publishers:")
    for pub, count in stats.most_common(30):
        print(f"  {count:4d}  {pub}")

    print(f"\nOutput: {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
