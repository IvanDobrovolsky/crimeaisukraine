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
    data = fetch_json(url, timeout=120)
    return data.get("results", {}).get("bindings", [])


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


def classify_religion(religion_qid: str, religion_label: str) -> str:
    """Classify religion from P140."""
    rl = religion_label.lower()
    if religion_qid in ("Q3333484", "Q35032"):
        return "Eastern Orthodoxy"
    if any(w in rl for w in ["orthodox", "православ"]):
        return "Eastern Orthodoxy"
    if any(w in rl for w in ["islam", "muslim", "іслам", "ислам", "sunni", "суні"]):
        return "Islam"
    if any(w in rl for w in ["catholic", "католи"]):
        return "Catholic"
    if any(w in rl for w in ["jewish", "judaism", "іудаїзм", "иудаизм"]):
        return "Judaism"
    if any(w in rl for w in ["karaite", "караїм"]):
        return "Karaism"
    if religion_label:
        return religion_label
    return "unspecified"


# ---------------------------------------------------------------------------
# SCAN 1: Wikidata religious institutions in Crimea
# ---------------------------------------------------------------------------

def scan_wikidata_institutions() -> dict:
    """Query Wikidata for all religious buildings in Crimea."""
    print("=" * 70)
    print("SCAN 1: Wikidata religious institutions in Crimea")
    print("=" * 70)

    # Strategy: three focused queries — one for Crimea, one for Sevastopol,
    # one for religious organizations / dioceses. Uses VALUES to enumerate
    # building types explicitly instead of P279* subclass traversal which
    # can time out or return massive cross-product results.
    # Q7835 = Crimea (ARC), Q7525 = Sevastopol

    all_rows = []

    # Query 1: Religious buildings in Crimea (P131+ Q7835)
    # Uses VALUES for building types to avoid P279* timeout
    query_crimea = """
SELECT DISTINCT ?item ?itemLabel ?typeLabel ?country ?countryLabel
       ?diocese ?dioceseLabel ?religion ?religionLabel
WHERE {
  ?item wdt:P131+ wd:Q7835 .
  ?item wdt:P31 ?type .
  VALUES ?type {
    wd:Q16970  wd:Q32815   wd:Q2977    wd:Q317557
    wd:Q108325 wd:Q44613   wd:Q1088552 wd:Q1509863
    wd:Q1128397 wd:Q56242820 wd:Q34627  wd:Q160742
    wd:Q4989906 wd:Q3947    wd:Q2031836 wd:Q1649060
  }
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P708 ?diocese }
  OPTIONAL { ?item wdt:P140 ?religion }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""
    print("\n  [1/5] Religious buildings in Crimea (VALUES types)...",
          end=" ", flush=True)
    rows1 = sparql_query(query_crimea)
    print(f"{len(rows1)} results")
    all_rows.extend(rows1)
    time.sleep(3)

    # Query 2: Religious buildings in Sevastopol (P131+ Q7525)
    query_sevastopol = """
SELECT DISTINCT ?item ?itemLabel ?typeLabel ?country ?countryLabel
       ?diocese ?dioceseLabel ?religion ?religionLabel
WHERE {
  ?item wdt:P131+ wd:Q7525 .
  ?item wdt:P31 ?type .
  VALUES ?type {
    wd:Q16970  wd:Q32815   wd:Q2977    wd:Q317557
    wd:Q108325 wd:Q44613   wd:Q1088552 wd:Q1509863
    wd:Q1128397 wd:Q56242820 wd:Q34627  wd:Q160742
    wd:Q4989906 wd:Q3947    wd:Q2031836 wd:Q1649060
  }
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P708 ?diocese }
  OPTIONAL { ?item wdt:P140 ?religion }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""
    print("  [2/5] Religious buildings in Sevastopol (VALUES types)...",
          end=" ", flush=True)
    rows2 = sparql_query(query_sevastopol)
    print(f"{len(rows2)} results")
    all_rows.extend(rows2)
    time.sleep(3)

    # Query 3: Also catch items using P279* but only for the top-level
    # religious building class (Q16970) in both locations. This catches
    # items typed as subclasses of religious building.
    query_subclass = """
SELECT DISTINCT ?item ?itemLabel ?typeLabel ?country ?countryLabel
       ?diocese ?dioceseLabel ?religion ?religionLabel
WHERE {
  {
    ?item wdt:P131+ wd:Q7835 .
  } UNION {
    ?item wdt:P131+ wd:Q7525 .
  }
  ?item wdt:P31/wdt:P279* wd:Q16970 .
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P708 ?diocese }
  OPTIONAL { ?item wdt:P140 ?religion }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""
    print("  [3/5] Religious buildings via subclass traversal...",
          end=" ", flush=True)
    rows3 = sparql_query(query_subclass)
    print(f"{len(rows3)} results")
    all_rows.extend(rows3)
    time.sleep(3)

    # Query 4: Religious organizations / dioceses in Crimea
    org_rows = []
    query_orgs = """
SELECT DISTINCT ?item ?itemLabel ?typeLabel ?country ?countryLabel ?hq ?hqLabel WHERE {
  {
    ?item wdt:P31/wdt:P279* wd:Q2061186 .
    ?item wdt:P131+ wd:Q7835 .
  } UNION {
    ?item wdt:P31/wdt:P279* wd:Q2061186 .
    ?item wdt:P159 ?hq .
    ?hq wdt:P131+ wd:Q7835 .
  } UNION {
    ?item wdt:P31/wdt:P279* wd:Q2061186 .
    ?item wdt:P131+ wd:Q7525 .
  }
  OPTIONAL { ?item wdt:P17 ?country }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""
    print("  [4/5] Religious organizations in Crimea + Sevastopol...",
          end=" ", flush=True)
    org_rows = sparql_query(query_orgs)
    print(f"{len(org_rows)} results")
    time.sleep(3)

    # Query 5: Dioceses covering Crimea
    diocese_rows = []
    query_dioceses = """
SELECT DISTINCT ?item ?itemLabel ?typeLabel ?country ?countryLabel ?parent ?parentLabel WHERE {
  {
    ?item wdt:P31/wdt:P279* wd:Q665487 .
    ?item wdt:P1001 wd:Q7835 .
  } UNION {
    ?item wdt:P31/wdt:P279* wd:Q665487 .
    ?item wdt:P1001 wd:Q7525 .
  } UNION {
    ?item wdt:P31/wdt:P279* wd:Q665487 .
    ?item wdt:P131+ wd:Q7835 .
  }
  OPTIONAL { ?item wdt:P17 ?country }
  OPTIONAL { ?item wdt:P749 ?parent }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru" }
}
"""
    print("  [5/5] Dioceses with jurisdiction over Crimea...",
          end=" ", flush=True)
    diocese_rows = sparql_query(query_dioceses)
    print(f"{len(diocese_rows)} results")

    # Dedup all building/institution results by QID
    seen = set()
    institutions = []

    for row in all_rows:
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

        # Classify religion
        religion_class = classify_religion(religion_qid, religion_label)

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
            "religion_class": religion_class,
        })

    # Process organizations
    org_seen = set()
    org_items = []
    for row in org_rows:
        qid = qid_from_uri(row.get("item", {}).get("value", ""))
        if not qid or qid in org_seen:
            continue
        org_seen.add(qid)
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

    # Process dioceses
    dioc_seen = set()
    diocese_items = []
    for row in diocese_rows:
        qid = qid_from_uri(row.get("item", {}).get("value", ""))
        if not qid or qid in dioc_seen:
            continue
        dioc_seen.add(qid)
        label = row.get("itemLabel", {}).get("value", "")
        type_label = row.get("typeLabel", {}).get("value", "")
        country_uri = row.get("country", {}).get("value", "")
        country_qid = qid_from_uri(country_uri)
        parent_label = row.get("parentLabel", {}).get("value", "")

        if country_qid == "Q212":
            country_class = "Ukraine"
        elif country_qid == "Q159":
            country_class = "Russia"
        elif country_qid:
            country_class = COUNTRY_NAMES.get(country_qid, country_qid)
        else:
            country_class = "missing"

        affiliation = classify_diocese(qid, label)

        diocese_items.append({
            "qid": qid,
            "label": label,
            "type": type_label,
            "country": country_class,
            "parent_org": parent_label,
            "affiliation": affiliation,
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
        r = inst["religion_class"]
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

    print(f"\n  Religion classification:")
    for k, v in sorted(religion_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    if org_items:
        print(f"\n  Religious organizations in Crimea: {len(org_items)}")
        for o in org_items:
            print(f"    - {o['label']} ({o['type']}) -- P17={o['country']}")

    if diocese_items:
        print(f"\n  Dioceses covering Crimea: {len(diocese_items)}")
        for d in diocese_items:
            print(f"    - {d['label']} ({d['type']}) -- P17={d['country']}, "
                  f"affiliation={d['affiliation']}, parent={d['parent_org']}")

    result = {
        "scan": "wikidata_religious_institutions",
        "date": datetime.now(timezone.utc).isoformat(),
        "total_institutions": len(institutions),
        "country_counts": country_counts,
        "diocese_affiliation_counts": diocese_counts,
        "religion_counts": religion_counts,
        "institutions": institutions,
        "organizations": org_items,
        "dioceses": diocese_items,
    }

    return result


# ---------------------------------------------------------------------------
# SCAN 2: Wikipedia articles on key Crimean religious sites
# ---------------------------------------------------------------------------

KEY_SITES = [
    {
        "name": "Chersonesus (ancient city)",
        "qid": "Q638445",
        "description": "Ancient Greek colony in Sevastopol, site of 'baptism of Rus'",
    },
    {
        "name": "St. Vladimir Cathedral, Sevastopol (admirals)",
        "qid": "Q1848287",
        "description": "Cathedral commemorating Russian navy admirals in Sevastopol",
    },
    {
        "name": "St. Vladimir Cathedral, Chersonesus",
        "qid": "Q166800",
        "description": "Cathedral built on the presumed site of Vladimir's baptism",
    },
    {
        "name": "Khan's Palace, Bakhchysarai",
        "qid": "Q743881",
        "description": "Crimean Tatar palace, UNESCO tentative list",
    },
    {
        "name": "Assumption Monastery (Uspensky)",
        "qid": "Q260494",
        "description": "Medieval cave monastery near Bakhchysarai",
    },
    {
        "name": "Juma-Jami Mosque, Yevpatoria",
        "qid": "Q2390721",
        "description": "16th-century mosque by Mimar Sinan",
    },
    {
        "name": "Kebir-Jami Mosque, Simferopol",
        "qid": "Q6382405",
        "description": "Oldest mosque in Simferopol",
    },
    {
        "name": "St. George Monastery, Balaklava",
        "qid": "Q12151107",
        "description": "Cave monastery near Balaklava, Sevastopol",
    },
]

LANGUAGES = ["en", "uk", "ru", "de", "fr"]


def classify_framing(description: str, extract: str) -> tuple[str, str]:
    """Classify framing of description + extract."""
    text = (description + " " + extract).lower()
    desc_lower = description.lower()

    label = "no_signal"
    signal = ""

    # Check description first (higher priority — it's what Google shows)
    if "ukraine" in desc_lower or "україн" in desc_lower:
        label = "ukraine"
        signal = "description mentions Ukraine"
    elif "russia" in desc_lower or "росі" in desc_lower or "росси" in desc_lower:
        label = "russia"
        signal = "description mentions Russia"

    # Check for admin names (overrides generic mention)
    if "republic of crimea" in desc_lower and "autonomous" not in desc_lower:
        label = "russia"
        signal = "uses 'Republic of Crimea' (Russian admin name)"
    if "autonomous republic" in desc_lower:
        label = "ukraine"
        signal = "uses 'Autonomous Republic' (Ukrainian admin name)"
    if "республика крым" in desc_lower:
        label = "russia"
        signal = "uses Russian admin name"
    if "автономна республіка" in desc_lower:
        label = "ukraine"
        signal = "uses Ukrainian admin name"

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


def get_sitelinks(qid: str) -> dict:
    """Fetch Wikidata entity and return sitelinks + P17."""
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    data = fetch_json(url)
    if not data:
        return {"sitelinks": {}, "countries": []}

    entity = data.get("entities", {}).get(qid, {})
    sitelinks = entity.get("sitelinks", {})

    # Also extract P17
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

    return {"sitelinks": sitelinks, "countries": countries}


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
            "sitelink_count": 0,
            "wikipedia_checks": [],
        }

        if not site["qid"]:
            print("    (no QID, skipping)")
            results.append(site_result)
            continue

        # Fetch entity data once — get sitelinks and P17
        print(f"  Fetching Wikidata entity {site['qid']}...")
        wd = get_sitelinks(site["qid"])
        sitelinks = wd["sitelinks"]
        countries = wd["countries"]

        site_result["wikidata_countries"] = countries
        site_result["sitelink_count"] = len(sitelinks)

        for c in countries:
            rank_str = f" (rank={c['rank']})" if c["rank"] else ""
            period = ""
            if c["start"] or c["end"]:
                period = f" [{c['start'] or '?'} -- {c['end'] or 'present'}]"
            print(f"    P17: {c['country']}{rank_str}{period}")
        if not countries:
            print("    P17: (none)")

        print(f"    Sitelinks: {len(sitelinks)} Wikipedia editions")
        time.sleep(0.5)

        # Check Wikipedia articles using sitelinks
        for lang in LANGUAGES:
            wiki_key = f"{lang}wiki"
            if wiki_key not in sitelinks:
                site_result["wikipedia_checks"].append({
                    "lang": lang,
                    "status": "no_sitelink",
                })
                print(f"    [{lang}] no sitelink")
                continue

            local_title = sitelinks[wiki_key]["title"]
            encoded = urllib.parse.quote(local_title.replace(" ", "_"))
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            data = fetch_json(url, timeout=15)

            if not data or "title" not in data:
                site_result["wikipedia_checks"].append({
                    "lang": lang,
                    "status": "api_error",
                    "sitelink_title": local_title,
                })
                print(f"    [{lang}] sitelink='{local_title}' but API returned no data")
                continue

            description = data.get("description", "")
            extract = data.get("extract", "")[:500]
            framing, signal = classify_framing(description, extract)

            check = {
                "lang": lang,
                "status": "found",
                "title": data.get("title", ""),
                "description": description,
                "extract_snippet": extract,
                "framing": framing,
                "signal": signal,
            }
            site_result["wikipedia_checks"].append(check)
            print(f"    [{lang}] title='{data.get('title','')}' "
                  f"desc=\"{description[:70]}\" => {framing}")
            time.sleep(0.5)

        results.append(site_result)

    # Compute summary
    framing_counts = {}
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
    cc = wikidata_result["country_counts"]
    dc = wikidata_result["diocese_affiliation_counts"]
    rc = wikidata_result["religion_counts"]
    print(f"  Wikidata institutions: {wikidata_result['total_institutions']}")
    print(f"    P17=Ukraine: {cc.get('Ukraine', 0)}")
    print(f"    P17=Russia:  {cc.get('Russia', 0)}")
    print(f"    P17=missing: {cc.get('missing', 0)}")
    for k, v in sorted(cc.items(), key=lambda x: -x[1]):
        if k not in ("Ukraine", "Russia", "missing"):
            print(f"    P17={k}: {v}")
    print(f"\n    Moscow Patriarchate dioceses: {dc.get('Moscow Patriarchate', 0)}")
    print(f"    OCU dioceses: {dc.get('OCU', 0)}")
    print(f"    UOC-MP dioceses: {dc.get('UOC-MP', 0)}")
    print(f"    No diocese: {dc.get('none', 0)}")
    print(f"    Other/unknown: {dc.get('other/unknown', 0)}")

    print(f"\n    Religion breakdown:")
    for k, v in sorted(rc.items(), key=lambda x: -x[1]):
        print(f"      {k}: {v}")

    fc = wikipedia_result["framing_counts"]
    ukraine_total = fc.get("ukraine", 0) + fc.get("ukraine_in_text", 0)
    russia_total = fc.get("russia", 0) + fc.get("russia_in_text", 0)
    print(f"\n  Wikipedia key sites: {len(wikipedia_result['sites'])}")
    print(f"    Ukraine-framed: {ukraine_total}")
    print(f"    Russia-framed:  {russia_total}")
    print(f"    Ambiguous:      {fc.get('ambiguous', 0)}")
    print(f"    No signal:      {fc.get('no_signal', 0)}")
    print(f"    No sitelink:    {fc.get('no_sitelink', 0)}")


if __name__ == "__main__":
    main()
