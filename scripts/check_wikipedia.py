"""
Wikipedia & Wikidata Crimea sovereignty audit.

Three checks per term per language:
1. Wikipedia description field (what Google shows in search results)
2. Wikidata country property (P17) — structured, unambiguous
3. Wikipedia categories — navigation hierarchy

Usage:
    python scripts/check_wikipedia.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"

CRIMEAN_CITIES = [
    ("Simferopol", "Q178149"),
    ("Sevastopol", "Q7525"),
    ("Yalta", "Q162629"),
    ("Kerch", "Q154438"),
    ("Feodosia", "Q156720"),
    ("Evpatoria", "Q156574"),
    ("Alushta", "Q155040"),
    ("Bakhchysarai", "Q156433"),
    ("Dzhankoy", "Q155949"),
    ("Sudak", "Q157067"),
    ("Armyansk", "Q156266"),
    ("Saky", "Q193925"),
    ("Inkerman", "Q756503"),
]

CRIMEAN_TERMS = [
    ("Crimea", "Q7835"),
    ("Crimean Peninsula", "Q7835"),
    ("Crimean Bridge", "Q16892386"),
    ("Crimean Tatars", "Q208801"),
]

LANGUAGES = ["en", "uk", "ru", "de", "fr", "it", "es", "pl", "tr", "ja", "zh", "ar"]
LANG_NAMES = {
    "en": "English", "uk": "Ukrainian", "ru": "Russian", "de": "German",
    "fr": "French", "it": "Italian", "es": "Spanish", "pl": "Polish",
    "tr": "Turkish", "ja": "Japanese", "zh": "Chinese", "ar": "Arabic",
}

HEADERS = {"User-Agent": "CrimeaAudit/1.0 (dobrovolsky94@gmail.com)"}


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except:
        return {}


def check_wikidata_country(qid: str) -> dict:
    """Check Wikidata P17 (country) claims for an entity."""
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    data = fetch_json(url)
    if not data:
        return {"qid": qid, "countries": []}

    entity = data.get("entities", {}).get(qid, {})
    claims = entity.get("claims", {})
    p17 = claims.get("P17", [])

    countries = []
    for claim in p17:
        mainsnak = claim.get("mainsnak", {})
        value = mainsnak.get("datavalue", {}).get("value", {})
        country_qid = value.get("id", "")

        # Resolve country name
        rank = claim.get("rank", "")
        qualifiers = claim.get("qualifiers", {})

        # Check for start/end time qualifiers
        start = ""
        end = ""
        for q in qualifiers.get("P580", []):
            start = q.get("datavalue", {}).get("value", {}).get("time", "")[:11]
        for q in qualifiers.get("P582", []):
            end = q.get("datavalue", {}).get("value", {}).get("time", "")[:11]

        country_name = {
            "Q212": "Ukraine",
            "Q159": "Russia",
            "Q15180": "Soviet Union",
            "Q12544": "Russian Empire",
            "Q12560": "Ottoman Empire",
        }.get(country_qid, country_qid)

        countries.append({
            "country": country_name,
            "qid": country_qid,
            "rank": rank,
            "start": start,
            "end": end,
        })

    return {"qid": qid, "countries": countries}


def check_wiki_description(term: str, lang: str) -> dict:
    """Check Wikipedia description field — what Google shows."""
    encoded = urllib.parse.quote(term.replace(" ", "_"))
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    data = fetch_json(url)
    if not data or "title" not in data:
        return {}

    description = data.get("description", "")
    extract = data.get("extract", "")[:300]

    # Classify the description (the Google preview)
    desc_lower = description.lower()
    label = "no_signal"
    signal = ""

    if "ukraine" in desc_lower or "україн" in desc_lower:
        label = "ukraine"
        signal = "description mentions Ukraine"
    elif "russia" in desc_lower or "росі" in desc_lower or "росси" in desc_lower:
        label = "russia"
        signal = "description mentions Russia"
    elif "crimea" in desc_lower and ("ukraine" not in desc_lower and "russia" not in desc_lower):
        label = "ambiguous"
        signal = "description mentions Crimea but no country"

    # Also check if description uses Russian admin name
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

    return {
        "description": description,
        "extract": extract,
        "label": label,
        "signal": signal,
        "url": f"https://{lang}.wikipedia.org/wiki/{encoded}",
    }


def check_wiki_categories(term: str, lang: str) -> dict:
    """Check Wikipedia categories for country hierarchy."""
    encoded = urllib.parse.quote(term.replace(" ", "_"))
    url = (f"https://{lang}.wikipedia.org/w/api.php?action=query&titles={encoded}"
           f"&prop=categories&cllimit=50&format=json")
    data = fetch_json(url)
    pages = data.get("query", {}).get("pages", {})

    categories = []
    for page in pages.values():
        for cat in page.get("categories", []):
            categories.append(cat.get("title", ""))

    cat_text = " ".join(categories).lower()
    has_ukraine = "ukraine" in cat_text or "україн" in cat_text or "украин" in cat_text
    has_russia = "russia" in cat_text or "росі" in cat_text or "росси" in cat_text

    if has_ukraine and not has_russia:
        cat_label = "ukraine"
    elif has_russia and not has_ukraine:
        cat_label = "russia"
    elif has_ukraine and has_russia:
        cat_label = "disputed"
    else:
        cat_label = "no_signal"

    return {
        "categories": categories[:10],
        "has_ukraine": has_ukraine,
        "has_russia": has_russia,
        "cat_label": cat_label,
    }


def main():
    all_terms = CRIMEAN_CITIES + CRIMEAN_TERMS
    results = []

    print(f"Wikipedia & Wikidata audit: {len(all_terms)} terms x {len(LANGUAGES)} languages")
    print("=" * 70)

    # Step 1: Wikidata P17 (country property)
    print("\n--- Wikidata P17 (country claims) ---")
    wikidata_results = {}
    for term, qid in all_terms:
        wd = check_wikidata_country(qid)
        wikidata_results[term] = wd

        current_countries = [c for c in wd["countries"] if c["rank"] == "preferred" or (not c["end"] and c["rank"] != "deprecated")]
        country_names = [c["country"] for c in current_countries]
        print(f"  {term:25s} ({qid}): {', '.join(country_names)}")
        time.sleep(0.2)

    # Step 2: Wikipedia descriptions + categories per language
    print("\n--- Wikipedia descriptions & categories ---")
    for term, qid in all_terms:
        for lang in LANGUAGES:
            desc = check_wiki_description(term, lang)
            if not desc:
                continue

            cats = check_wiki_categories(term, lang)

            entry = {
                "term": term,
                "qid": qid,
                "language": lang,
                "language_name": LANG_NAMES.get(lang, lang),
                "wikidata_countries": [c["country"] for c in wikidata_results.get(term, {}).get("countries", []) if c["rank"] != "deprecated"],
                **desc,
                "cat_label": cats["cat_label"],
                "categories_ukraine": cats["has_ukraine"],
                "categories_russia": cats["has_russia"],
            }
            results.append(entry)

            if entry["label"] != "no_signal":
                icon = {"ukraine": "U", "russia": "R", "disputed": "D", "ambiguous": "?"}.get(entry["label"], ".")
                print(f"  {icon} [{lang:2s}] {term:20s} desc={entry['label']:8s} cat={cats['cat_label']:8s} | {entry['description'][:50]}")

            time.sleep(0.1)

    # Summary
    print(f"\n{'='*70}")
    print(f"RESULTS: {len(results)} entries")

    # By language: how descriptions classify cities
    print(f"\nDescription classification by language:")
    by_lang = {}
    for r in results:
        lang = r["language_name"]
        label = r["label"]
        if label == "no_signal":
            continue
        by_lang.setdefault(lang, {"ukraine": 0, "russia": 0, "disputed": 0, "ambiguous": 0})
        by_lang[lang][label] = by_lang[lang].get(label, 0) + 1

    for lang in sorted(by_lang.keys(), key=lambda x: -by_lang[x].get("russia", 0)):
        c = by_lang[lang]
        print(f"  {lang:12s}: UA={c.get('ukraine',0):2d}  RU={c.get('russia',0):2d}  D={c.get('disputed',0):2d}  ?={c.get('ambiguous',0):2d}")

    # Wikidata summary
    print(f"\nWikidata P17 (structured country claims):")
    for term, qid in all_terms:
        countries = wikidata_results.get(term, {}).get("countries", [])
        current = [c for c in countries if c["rank"] != "deprecated" and not c.get("end")]
        names = [c["country"] for c in current]
        both = "Ukraine" in names and "Russia" in names
        status = "BOTH (disputed)" if both else "Ukraine only" if "Ukraine" in names else "Russia only" if "Russia" in names else "other"
        print(f"  {term:25s}: {status} — {names}")

    # Russia-framing descriptions
    ru_desc = [r for r in results if r["label"] == "russia"]
    if ru_desc:
        print(f"\nRussia-framing descriptions ({len(ru_desc)}):")
        for r in ru_desc:
            print(f"  [{r['language']:2s}] {r['term']:20s} | \"{r['description'][:60]}\"")
            print(f"       Signal: {r['signal']}")
            print(f"       {r['url']}")

    # Save
    output = DATA / "wikipedia_audit.json"
    with open(output, "w") as f:
        json.dump({
            "total_entries": len(results),
            "by_language": by_lang,
            "wikidata": wikidata_results,
            "russia_framing": ru_desc,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {output}")


if __name__ == "__main__":
    main()
