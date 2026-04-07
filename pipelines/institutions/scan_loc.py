"""
Library of Congress Crimea sovereignty audit.

Checks:
1. LCSH subject headings — canonical form for "Crimea"
2. Catalog search — how books about Crimea are classified
3. Names authority — canonical geographic names

Usage:
    python scripts/check_loc.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
HEADERS = {"User-Agent": "CrimeaAudit/1.0 (dobrovolsky94@gmail.com)"}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error: {e}")
        return {}


def check_subject_headings():
    """Check LCSH subject headings for Crimea."""
    print("--- LCSH Subject Headings ---")
    url = "https://id.loc.gov/authorities/subjects/suggest2?q=Crimea&count=50"
    data = fetch_json(url)
    hits = data.get("hits", [])

    results = []
    ua_count = 0
    ru_count = 0
    for h in hits:
        label = h.get("aLabel", "")
        uri = h.get("uri", "")
        has_ukraine = "ukraine" in label.lower()
        has_russia = "russia" in label.lower() and "ukraine" not in label.lower()
        if has_ukraine:
            ua_count += 1
        if has_russia:
            ru_count += 1
        results.append({"label": label, "uri": uri, "ukraine": has_ukraine, "russia": has_russia})

    print(f"  Total headings: {len(results)}")
    print(f"  Mentioning Ukraine: {ua_count}")
    print(f"  Mentioning Russia (w/o Ukraine): {ru_count}")
    return results


def check_geographic_headings():
    """Check canonical geographic form for Crimean places."""
    print("\n--- Geographic Authority Headings ---")
    terms = ["Crimea (Ukraine)", "Simferopol", "Sevastopol", "Yalta", "Kerch"]
    results = []

    for term in terms:
        encoded = urllib.parse.quote(term)
        # Try subjects
        url = f"https://id.loc.gov/authorities/subjects/suggest2?q={encoded}&count=10"
        data = fetch_json(url)
        for h in data.get("hits", [])[:5]:
            label = h.get("aLabel", "")
            results.append({"query": term, "type": "subject", "label": label, "uri": h.get("uri", "")})
            print(f"  [subject] {term} → {label}")

        # Try names
        url2 = f"https://id.loc.gov/authorities/names/suggest2?q={encoded}&count=10"
        data2 = fetch_json(url2)
        for h in data2.get("hits", [])[:5]:
            label = h.get("aLabel", "")
            results.append({"query": term, "type": "name", "label": label, "uri": h.get("uri", "")})
            print(f"  [name]    {term} → {label}")

        time.sleep(0.3)
    return results


def check_catalog():
    """Search LoC catalog for books about Crimea."""
    print("\n--- Catalog Search ---")
    all_results = []
    offsets = [0, 50, 100]

    for offset in offsets:
        url = f"https://www.loc.gov/search/?q=crimea&fo=json&c=50&sp={offset // 50 + 1}&fa=partof:catalog"
        data = fetch_json(url)
        items = data.get("results", [])
        if not items:
            break

        for r in items:
            title = r.get("title", "")
            subjects = r.get("subject", []) or []
            locations = r.get("location", []) or []
            date = r.get("date", "")

            subj_text = " ".join(subjects).lower() if isinstance(subjects, list) else str(subjects).lower()
            loc_text = " ".join(locations).lower() if isinstance(locations, list) else str(locations).lower()
            all_text = f"{subj_text} {loc_text}"

            has_ua = "ukraine" in all_text
            has_ru = "russia" in all_text

            label = "ukraine" if has_ua and not has_ru else "russia" if has_ru and not has_ua else "both" if has_ua and has_ru else "neither"

            all_results.append({
                "title": title[:200],
                "date": date,
                "subjects": subjects[:10] if isinstance(subjects, list) else [],
                "locations": locations[:5] if isinstance(locations, list) else [],
                "label": label,
            })
        time.sleep(0.5)

    # Stats
    from collections import Counter
    labels = Counter(r["label"] for r in all_results)
    print(f"  Total books: {len(all_results)}")
    for k, v in labels.most_common():
        print(f"    {k}: {v}")

    return all_results, dict(labels)


def main():
    print("Library of Congress Crimea Sovereignty Audit")
    print("=" * 60)

    headings = check_subject_headings()
    geo = check_geographic_headings()
    catalog, catalog_stats = check_catalog()

    # Key findings
    key_headings = [h for h in headings if "ukraine" in h["label"].lower() or "occupation" in h["label"].lower()]

    output = {
        "source": "Library of Congress",
        "date": __import__("datetime").datetime.now().isoformat()[:10],
        "subject_headings": {
            "total": len(headings),
            "ukraine_mentions": sum(1 for h in headings if h["ukraine"]),
            "russia_only_mentions": sum(1 for h in headings if h["russia"]),
            "key_headings": [h["label"] for h in key_headings],
            "all_headings": headings,
        },
        "geographic_authority": geo,
        "catalog": {
            "total_books": len(catalog),
            "by_label": catalog_stats,
            "books": catalog,
        },
        "findings": {
            "canonical_form": "Crimea (Ukraine)",
            "occupation_heading": "Crimea (Ukraine)--History--Russian occupation, 2014-",
            "sevastopol_form": "Sevastopolʹ (Ukraine)",
            "catalog_ukraine_pct": round(100 * catalog_stats.get("ukraine", 0) / max(len(catalog), 1), 1),
        },
    }

    out_path = DATA / "loc_crimea.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
