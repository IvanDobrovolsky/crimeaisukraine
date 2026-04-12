"""
Religious institutions in Crimea — Wikidata + Wikipedia audit.

SCAN 1: Wikidata SPARQL queries for churches, monasteries, cathedrals, mosques
         in Crimea. Checks P17 (country), P708 (diocese), and diocese affiliation
         (Moscow Patriarchate vs OCU vs other).

SCAN 2: Wikipedia REST API checks for key Crimean religious sites — description
         field and first-paragraph framing analysis.

Usage:
    cd pipelines/religious && uv run scan_wikidata.py
"""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).parent
DATA = PROJECT / "data"
DATA.mkdir(exist_ok=True)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "CrimeaAudit/1.0 (dobrovolsky94@gmail.com)"}

# Known QIDs for classification
COUNTRY_NAMES = {
    "Q212": "Ukraine",
    "Q159": "Russia",
    "Q15180": "Soviet Union",
    "Q12544": "Russian Empire",
    "Q12560": "Ottoman Empire",
    "Q7835": "Crimea",
}

# Known diocese/church affiliations
MOSCOW_PATRIARCHATE_QIDS = {
    "Q170045",   # Russian Orthodox Church (Moscow Patriarchate)
    "Q1820179",  # Diocese of Simferopol and Crimea (ROC)
    "Q4187438",  # Dzhankoy diocese (ROC)
    "Q4536261",  # Feodosia diocese (ROC)
}

OCU_QIDS = {
    "Q56330486",  # Orthodox Church of Ukraine
}

UOC_MP_QIDS = {
    "Q756898",   # Ukrainian Orthodox Church (Moscow Patriarchate)
}

UGCC_QIDS = {
    "Q183393",   # Ukrainian Greek Catholic Church
}


def fetch_json(url: str, timeout: int = 90) -> dict:
    """Fetch JSON from URL with retry."""
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt == 2:
                print(f"    fetch_json failed after 3 attempts: {e}")
                return {}
            print(f"    fetch_json attempt {attempt+1} failed: {e}, retrying...")
            time.sleep(2 * (attempt + 1))
    return {}


def sparql_query(query: str) -> list[dict]:
    """Run a SPARQL query against the Wikidata endpoint."""
    url = f"{SPARQL_ENDPOINT}?query={urllib.parse.quote(query)}&format=json"
    data = fetch_json(url)
    return data.get("results", {}).get("bindings", [])


# ---------------------------------------------------------------------------
# SCAN 1: Wikidata religious institutions in Crimea
# ---------------------------------------------------------------------------

def qid_from_uri(uri: str) -> str:
    """Extract QID from Wikidata entity URI."""
    if uri and "/" in uri:
        return uri.rsplit("/", 1)[-1]
    return ""


def classify_diocese(diocese_qid: str, diocese_label: str) -> str:
    """Classify a diocese as Moscow Patriarchate, OCU, or other."""
    if diocese_qid in MOSCOW_PATRIARCHATE_QIDS:
        return "Moscow Patriarchate"
    if diocese_qid in OCU_QIDS:
        return "OCU"
    if diocese_qid in UOC_MP_QIDS:
        return "UOC-MP"
    if diocese_qid in UGCC_QIDS:
        return "UGCC"
    label_lower = diocese_label.lower()
    if any(w in label_lower for w in ["moscow", "russian orthodox", "московск", "руськ"]):
        return "Moscow Patriarchate"
    if any(w in label_lower for w in ["orthodox church of ukraine", "православна церква україни"]):
        return "OCU"
    if any(w in label_lower for w in ["greek catholic", "греко-католи"]):
        return "UGCC"
    if any(w in label_lower for w in ["islam", "muslim", "мусульман", "мечеть"]):
        return "Islamic"
    return "other/unknown"


def scan_wikidata_institutions() -> dict:
    """Query Wikidata for all religious buildings in Crimea."""
    print("=" * 70)
    print("SCAN 1: Wikidata religious institutions in Crimea")
    print("=" * 70)

    # Main query: religious buildings located in Crimea (P131 chain)
    # Q16970 = religious building (includes churches, mosques, etc.)
    # Q7835 = Crimea
    query_buildings = """
SELECT ?item ?itemLabel ?typeLabel ?country ?countryLabel ?diocese ?dioceseLabel ?religion ?religionLabel WHERE {
  ?item wdt:P131+ wd:Q7835 .
  ?item wdt:P31/wdt:P279* wd:Q16970 .
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P708 ?diocese }
  OPTIONAL { ?item wdt:P140 ?religion }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""

    print("\n[1/4] Querying religious buildings in Crimea (P131+ Q7835)...")
    buildings = sparql_query(query_buildings)
    print(f"  Found {len(buildings)} results")

    # Also query for Sevastopol (separate admin unit)
    query_sevastopol = """
SELECT ?item ?itemLabel ?typeLabel ?country ?countryLabel ?diocese ?dioceseLabel ?religion ?religionLabel WHERE {
  ?item wdt:P131+ wd:Q7525 .
  ?item wdt:P31/wdt:P279* wd:Q16970 .
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P708 ?diocese }
  OPTIONAL { ?item wdt:P140 ?religion }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""

    print("\n[2/4] Querying religious buildings in Sevastopol (P131+ Q7525)...")
    time.sleep(2)  # Be polite to Wikidata
    sevastopol = sparql_query(query_sevastopol)
    print(f"  Found {len(sevastopol)} results")

    # Query for religious organizations/dioceses covering Crimea
    query_orgs = """
SELECT ?item ?itemLabel ?typeLabel ?country ?countryLabel ?hq ?hqLabel WHERE {
  {
    ?item wdt:P31/wdt:P279* wd:Q2061186 .
    ?item wdt:P131+ wd:Q7835 .
  } UNION {
    ?item wdt:P31/wdt:P279* wd:Q2061186 .
    ?item wdt:P159 ?hq .
    ?hq wdt:P131+ wd:Q7835 .
  }
  OPTIONAL { ?item wdt:P17 ?country }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""

    print("\n[3/4] Querying religious organizations in Crimea...")
    time.sleep(2)
    orgs = sparql_query(query_orgs)
    print(f"  Found {len(orgs)} results")

    # Also query monasteries specifically (Q44613)
    query_monasteries = """
SELECT ?item ?itemLabel ?typeLabel ?country ?countryLabel ?diocese ?dioceseLabel ?religion ?religionLabel WHERE {
  {
    ?item wdt:P131+ wd:Q7835 .
    ?item wdt:P31/wdt:P279* wd:Q44613 .
  } UNION {
    ?item wdt:P131+ wd:Q7525 .
    ?item wdt:P31/wdt:P279* wd:Q44613 .
  }
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P708 ?diocese }
  OPTIONAL { ?item wdt:P140 ?religion }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""

    print("\n[4/4] Querying monasteries in Crimea + Sevastopol...")
    time.sleep(2)
    monasteries = sparql_query(query_monasteries)
    print(f"  Found {len(monasteries)} results")

    # Merge all results, dedup by QID
    all_results = buildings + sevastopol + monasteries
    seen = set()
    institutions = []

    for row in all_results:
        qid = qid_from_uri(row.get("item", {}).get("value", ""))
        if not qid or qid in seen:
            continue
        seen.add(qid)

        label = row.get("itemLabel", {}).get("value", "")
        type_label = row.get("typeLabel", {}).get("value", "")
        country_uri = row.get("country", {}).get("value", "")
        country_qid = qid_from_uri(country_uri)
        country_label = row.get("countryLabel", {}).get("value", "")
        diocese_uri = row.get("diocese", {}).get("value", "")
        diocese_qid = qid_from_uri(diocese_uri)
        diocese_label = row.get("dioceseLabel", {}).get("value", "")
        religion_uri = row.get("religion", {}).get("value", "")
        religion_qid = qid_from_uri(religion_uri)
        religion_label = row.get("religionLabel", {}).get("value", "")

        # Classify country
        if country_qid == "Q212":
            country_class = "Ukraine"
        elif country_qid == "Q159":
            country_class = "Russia"
        elif country_qid:
            country_class = COUNTRY_NAMES.get(country_qid, country_label or country_qid)
        else:
            country_class = "missing"

        # Classify diocese affiliation
        diocese_class = classify_diocese(diocese_qid, diocese_label) if diocese_qid else "none"

        institutions.append({
            "qid": qid,
            "label": label,
            "type": type_label,
            "country_qid": country_qid,
            "country": country_class,
            "diocese_qid": diocese_qid,
            "diocese_label": diocese_label,
            "diocese_affiliation": diocese_class,
            "religion_qid": religion_qid,
            "religion_label": religion_label,
        })

    # Process organizations
    org_items = []
    for row in orgs:
        qid = qid_from_uri(row.get("item", {}).get("value", ""))
        if not qid:
            continue
        label = row.get("itemLabel", {}).get("value", "")
        type_label = row.get("typeLabel", {}).get("value", "")
        country_uri = row.get("country", {}).get("value", "")
        country_qid = qid_from_uri(country_uri)
        country_label = row.get("countryLabel", {}).get("value", "")
        hq_label = row.get("hqLabel", {}).get("value", "")

        if country_qid == "Q212":
            country_class = "Ukraine"
        elif country_qid == "Q159":
            country_class = "Russia"
        elif country_qid:
            country_class = COUNTRY_NAMES.get(country_qid, country_label or country_qid)
        else:
            country_class = "missing"

        org_items.append({
            "qid": qid,
            "label": label,
            "type": type_label,
            "country": country_class,
            "headquarters": hq_label,
        })

    # Compute counts
    country_counts = {}
    for inst in institutions:
        c = inst["country"]
        country_counts[c] = country_counts.get(c, 0) + 1

    diocese_counts = {}
    for inst in institutions:
        d = inst["diocese_affiliation"]
        diocese_counts[d] = diocese_counts.get(d, 0) + 1

    religion_counts = {}
    for inst in institutions:
        r = inst["religion_label"] or "unspecified"
        religion_counts[r] = religion_counts.get(r, 0) + 1

    # Print summary
    print("\n" + "=" * 70)
    print(f"WIKIDATA RESULTS: {len(institutions)} religious institutions in Crimea")
    print("=" * 70)

    print(f"\n  P17 (country) distribution:")
    for k, v in sorted(country_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    print(f"\n  Diocese affiliation distribution:")
    for k, v in sorted(diocese_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    print(f"\n  Religion (P140) distribution:")
    for k, v in sorted(religion_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    if org_items:
        print(f"\n  Religious organizations in Crimea: {len(org_items)}")
        for o in org_items:
            print(f"    - {o['label']} ({o['type']}) — P17={o['country']}")

    result = {
        "scan": "wikidata_religious_institutions",
        "date": datetime.now(timezone.utc).isoformat(),
        "total_institutions": len(institutions),
        "country_counts": country_counts,
        "diocese_affiliation_counts": diocese_counts,
        "religion_counts": religion_counts,
        "institutions": institutions,
        "organizations": org_items,
    }

    return result


# ---------------------------------------------------------------------------
# SCAN 2: Wikipedia articles on key Crimean religious sites
# ---------------------------------------------------------------------------

KEY_SITES = [
    {
        "name": "Chersonesus",
        "qid": "Q184948",
        "en_title": "Chersonesus",
        "description": "Ancient Greek colony, site of 'baptism of Rus'",
    },
    {
        "name": "St. Vladimir Cathedral, Sevastopol",
        "qid": "Q4187523",
        "en_title": "Saint_Vladimir_Cathedral_(Sevastopol)",
        "description": "Cathedral commemorating baptism of Vladimir",
    },
    {
        "name": "Khan's Palace, Bakhchysarai",
        "qid": "Q937457",
        "en_title": "Bakhchysarai_Palace",
        "description": "Crimean Tatar palace, UNESCO tentative list",
    },
    {
        "name": "Assumption Monastery (Uspensky)",
        "qid": "Q4018729",
        "en_title": "Assumption_Monastery_of_the_Caves",
        "description": "Medieval cave monastery near Bakhchysarai",
    },
    {
        "name": "New Chersonesos complex",
        "qid": None,
        "en_title": None,
        "description": "Russian state/church project on UNESCO site (opened 2024)",
    },
    {
        "name": "St. Vladimir Cathedral, Chersonesus",
        "qid": "Q4187522",
        "en_title": "Saint_Vladimir_Cathedral,_Chersonesus",
        "description": "Cathedral built on the presumed site of Vladimir's baptism",
    },
    {
        "name": "Juma-Jami Mosque, Yevpatoria",
        "qid": "Q4131693",
        "en_title": "Juma-Jami",
        "description": "16th-century mosque by Mimar Sinan",
    },
    {
        "name": "Kebir-Jami Mosque, Simferopol",
        "qid": "Q4222427",
        "en_title": "Kebir-Jami",
        "description": "Oldest mosque in Simferopol",
    },
]

LANGUAGES = ["en", "uk", "ru", "de", "fr"]


def classify_framing(description: str, extract: str) -> tuple[str, str]:
    """Classify framing of description + extract as ukraine/russia/ambiguous/no_signal."""
    text = (description + " " + extract).lower()

    label = "no_signal"
    signal = ""

    # Check description first (higher priority — it's what Google shows)
    desc_lower = description.lower()

    if "ukraine" in desc_lower or "україн" in desc_lower:
        label = "ukraine"
        signal = "description mentions Ukraine"
    elif "russia" in desc_lower or "росі" in desc_lower or "росси" in desc_lower:
        label = "russia"
        signal = "description mentions Russia"

    # Check for admin names
    if "republic of crimea" in desc_lower and "autonomous" not in desc_lower:
        label = "russia"
        signal = "uses 'Republic of Crimea' (Russian admin name)"
    if "autonomous republic" in desc_lower:
        label = "ukraine"
        signal = "uses 'Autonomous Republic' (Ukrainian admin name)"
    if "республика крым" in desc_lower:
        label = "russia"
        signal = "uses 'Республика Крым' (Russian admin name)"
    if "автономна республіка" in desc_lower:
        label = "ukraine"
        signal = "uses 'Автономна Республіка' (Ukrainian admin name)"

    # If description is neutral, check extract
    if label == "no_signal":
        if "ukraine" in text or "україн" in text:
            label = "ukraine_in_text"
            signal = "first paragraph mentions Ukraine"
        elif "russia" in text or "росі" in text or "росси" in text:
            label = "russia_in_text"
            signal = "first paragraph mentions Russia"
        elif "crimea" in text or "крим" in text:
            label = "ambiguous"
            signal = "mentions Crimea but no country attribution"

    return label, signal


def check_wikidata_country(qid: str) -> list[dict]:
    """Check P17 (country) claims on a Wikidata entity."""
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    data = fetch_json(url)
    if not data:
        return []

    entity = data.get("entities", {}).get(qid, {})
    claims = entity.get("claims", {})
    p17 = claims.get("P17", [])

    countries = []
    for claim in p17:
        mainsnak = claim.get("mainsnak", {})
        value = mainsnak.get("datavalue", {}).get("value", {})
        country_qid = value.get("id", "")
        rank = claim.get("rank", "")
        qualifiers = claim.get("qualifiers", {})

        start = ""
        end = ""
        for q in qualifiers.get("P580", []):
            start = q.get("datavalue", {}).get("value", {}).get("time", "")[:11]
        for q in qualifiers.get("P582", []):
            end = q.get("datavalue", {}).get("value", {}).get("time", "")[:11]

        country_name = COUNTRY_NAMES.get(country_qid, country_qid)
        countries.append({
            "country": country_name,
            "qid": country_qid,
            "rank": rank,
            "start": start,
            "end": end,
        })

    return countries


def scan_wikipedia_sites() -> dict:
    """Check Wikipedia description/framing for key Crimean religious sites."""
    print("\n" + "=" * 70)
    print("SCAN 2: Wikipedia articles on key Crimean religious sites")
    print("=" * 70)

    results = []

    for site in KEY_SITES:
        print(f"\n  --- {site['name']} ---")
        site_result = {
            "name": site["name"],
            "qid": site["qid"],
            "note": site["description"],
            "wikidata_countries": [],
            "wikipedia_checks": [],
        }

        # Check Wikidata P17 if we have a QID
        if site["qid"]:
            print(f"  Checking Wikidata P17 for {site['qid']}...")
            countries = check_wikidata_country(site["qid"])
            site_result["wikidata_countries"] = countries
            for c in countries:
                rank_str = f" (rank={c['rank']})" if c['rank'] else ""
                period = ""
                if c['start'] or c['end']:
                    period = f" [{c['start'] or '?'} — {c['end'] or 'present'}]"
                print(f"    P17: {c['country']}{rank_str}{period}")
            if not countries:
                print(f"    P17: (none)")
            time.sleep(1)

        # Check Wikipedia in multiple languages
        if site.get("en_title"):
            for lang in LANGUAGES:
                # Try the English title first (most reliable), adjust for language
                title = site["en_title"]
                encoded = urllib.parse.quote(title)
                url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
                data = fetch_json(url, timeout=15)

                if not data or "title" not in data:
                    # Try to find via Wikidata sitelinks
                    if site["qid"]:
                        sitelink_url = f"https://www.wikidata.org/wiki/Special:EntityData/{site['qid']}.json"
                        wd_data = fetch_json(sitelink_url)
                        if wd_data:
                            entity = wd_data.get("entities", {}).get(site["qid"], {})
                            sitelinks = entity.get("sitelinks", {})
                            wiki_key = f"{lang}wiki"
                            if wiki_key in sitelinks:
                                local_title = sitelinks[wiki_key]["title"]
                                encoded_local = urllib.parse.quote(local_title.replace(" ", "_"))
                                url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_local}"
                                data = fetch_json(url, timeout=15)

                if not data or "title" not in data:
                    site_result["wikipedia_checks"].append({
                        "lang": lang,
                        "status": "not_found",
                    })
                    continue

                description = data.get("description", "")
                extract = data.get("extract", "")[:500]
                label, signal = classify_framing(description, extract)

                check = {
                    "lang": lang,
                    "status": "found",
                    "title": data.get("title", ""),
                    "description": description,
                    "extract_snippet": extract,
                    "framing": label,
                    "signal": signal,
                }
                site_result["wikipedia_checks"].append(check)
                print(f"    [{lang}] desc=\"{description[:80]}\" => {label}")
                time.sleep(0.5)
        else:
            print(f"    (no Wikipedia article title configured — skipping Wikipedia check)")

        results.append(site_result)

    # Compute summary
    framing_counts = {"ukraine": 0, "russia": 0, "ambiguous": 0, "no_signal": 0,
                      "ukraine_in_text": 0, "russia_in_text": 0, "not_found": 0}
    for site in results:
        for check in site.get("wikipedia_checks", []):
            f = check.get("framing", check.get("status", "not_found"))
            framing_counts[f] = framing_counts.get(f, 0) + 1

    p17_summary = {"Ukraine": 0, "Russia": 0, "other": 0, "none": 0}
    for site in results:
        countries = site.get("wikidata_countries", [])
        if not countries:
            p17_summary["none"] += 1
        for c in countries:
            cn = c["country"]
            if cn == "Ukraine":
                p17_summary["Ukraine"] += 1
            elif cn == "Russia":
                p17_summary["Russia"] += 1
            else:
                p17_summary["other"] += 1

    print("\n" + "=" * 70)
    print("WIKIPEDIA FRAMING SUMMARY (key religious sites)")
    print("=" * 70)
    print(f"\n  Description/extract framing across {len(LANGUAGES)} languages:")
    for k, v in sorted(framing_counts.items(), key=lambda x: -x[1]):
        if v > 0:
            print(f"    {k}: {v}")

    print(f"\n  Wikidata P17 on key sites:")
    for k, v in sorted(p17_summary.items(), key=lambda x: -x[1]):
        if v > 0:
            print(f"    {k}: {v}")

    return {
        "scan": "wikipedia_religious_sites",
        "date": datetime.now(timezone.utc).isoformat(),
        "languages_checked": LANGUAGES,
        "sites": results,
        "framing_counts": framing_counts,
        "p17_summary": p17_summary,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"Religious institutions scan started at {ts}")
    print(f"Output directory: {DATA}")

    # SCAN 1
    wikidata_result = scan_wikidata_institutions()

    outfile1 = DATA / "wikidata_religious.json"
    with open(outfile1, "w") as f:
        json.dump(wikidata_result, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {outfile1}")

    # SCAN 2
    wikipedia_result = scan_wikipedia_sites()

    outfile2 = DATA / "wikipedia_religious.json"
    with open(outfile2, "w") as f:
        json.dump(wikipedia_result, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {outfile2}")

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Wikidata institutions: {wikidata_result['total_institutions']}")
    print(f"    P17=Ukraine: {wikidata_result['country_counts'].get('Ukraine', 0)}")
    print(f"    P17=Russia:  {wikidata_result['country_counts'].get('Russia', 0)}")
    print(f"    P17=missing: {wikidata_result['country_counts'].get('missing', 0)}")
    print(f"    Moscow Patriarchate dioceses: {wikidata_result['diocese_affiliation_counts'].get('Moscow Patriarchate', 0)}")
    print(f"    OCU dioceses: {wikidata_result['diocese_affiliation_counts'].get('OCU', 0)}")
    print(f"    UOC-MP dioceses: {wikidata_result['diocese_affiliation_counts'].get('UOC-MP', 0)}")
    print(f"    No diocese: {wikidata_result['diocese_affiliation_counts'].get('none', 0)}")
    print(f"  Wikipedia key sites: {len(wikipedia_result['sites'])}")
    fc = wikipedia_result["framing_counts"]
    ukraine_total = fc.get("ukraine", 0) + fc.get("ukraine_in_text", 0)
    russia_total = fc.get("russia", 0) + fc.get("russia_in_text", 0)
    print(f"    Ukraine-framed: {ukraine_total}")
    print(f"    Russia-framed:  {russia_total}")
    print(f"    Ambiguous:      {fc.get('ambiguous', 0)}")
    print(f"    No signal:      {fc.get('no_signal', 0)}")
    print(f"    Not found:      {fc.get('not_found', 0)}")


if __name__ == "__main__":
    main()
