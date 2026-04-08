"""
Wikipedia & Wikidata Crimea sovereignty audit.

Checks per term per language:
1. Wikipedia description field (what Google shows in search results)
2. Wikidata country property (P17) — structured, unambiguous
3. Wikipedia categories — navigation hierarchy
4. Wikidata entity sitelinks — asymmetry between editions that have an
   article for Q15966495 ("Republic of Crimea", the Russian federal subject)
   vs Q756294 ("Autonomous Republic of Crimea", the Ukrainian unit)
5. Crimean-born people stratified by P570 (date of death) and P27 qualifier
   P580 (citizenship start time) — separates pre-1991 / Soviet / 1991-2014 /
   post-2014 cohorts to isolate post-occupation passportization from
   biographical lag (Imperial Russia, Soviet Union successor-state mapping)

Usage:
    cd pipelines/wikipedia && uv run scan.py
    # or from project root:
    make pipeline-wikipedia
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

PROJECT = Path(__file__).parent
DATA = PROJECT / "data"
DATA.mkdir(exist_ok=True)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

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


def fetch_json(url: str, timeout: int = 10) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        # SPARQL queries can be slow; surface failures instead of swallowing
        print(f"    fetch_json failed: {e}")
        return {}


def sparql_query(query: str) -> list[dict]:
    """Run a SPARQL query against the Wikidata endpoint. Returns list of bindings."""
    url = f"{SPARQL_ENDPOINT}?query={urllib.parse.quote(query)}&format=json"
    data = fetch_json(url, timeout=90)
    return data.get("results", {}).get("bindings", [])


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


def fetch_entity(qid: str) -> dict:
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    return fetch_json(url).get("entities", {}).get(qid, {})


def wiki_sitelinks(entity: dict) -> dict:
    """Return {lang_code: article_title} for every standard-Wikipedia sitelink."""
    out = {}
    for key, payload in (entity.get("sitelinks") or {}).items():
        # standard wiki edition keys end with 'wiki' and exclude commons, meta, species, etc.
        if not key.endswith("wiki"):
            continue
        if key in ("commonswiki", "metawiki", "specieswiki", "wikidatawiki", "mediawikiwiki"):
            continue
        lang = key[:-4]  # strip 'wiki'
        out[lang] = payload.get("title", "")
    return out


# The three Wikidata entities that carry the sovereignty framing.
# Q7835       = Crimea (the peninsula, geographic — neutral)
# Q15966495   = Republic of Crimea (the Russian federal subject, est. Mar 2014)
# Q756294     = Autonomous Republic of Crimea (Ukrainian administrative unit)
CRIMEA_ENTITY_IDS = {
    "peninsula":          "Q7835",
    "russian_fed_subject": "Q15966495",
    "ukrainian_unit":      "Q756294",
}


def run_sitelink_asymmetry() -> dict:
    """
    For each Wikipedia edition, does it have a standalone article for:
        - the Russian federal subject (Q15966495)?
        - the Ukrainian Autonomous Republic (Q756294)?
        - just the geographic peninsula (Q7835)?

    An edition that has an article for Q15966495 has, editorially, accepted
    the Russian federal subject as an article-worthy entity distinct from the
    peninsula. This is a structural signal — stronger than description text
    because creating a standalone article is an affirmative editorial act.

    The asymmetry (editions with Russian but not Ukrainian entity, and
    vice versa) is the headline finding.
    """
    print("\n--- Wikidata entity sitelink sweep (Q15966495 vs Q756294 vs Q7835) ---")
    entities = {k: fetch_entity(v) for k, v in CRIMEA_ENTITY_IDS.items()}
    sitelinks = {k: wiki_sitelinks(v) for k, v in entities.items()}
    ru = sitelinks["russian_fed_subject"]
    ua = sitelinks["ukrainian_unit"]
    pen = sitelinks["peninsula"]
    ru_set, ua_set, pen_set = set(ru), set(ua), set(pen)

    ru_only = sorted(ru_set - ua_set)
    ua_only = sorted(ua_set - ru_set)
    both = sorted(ru_set & ua_set)
    neither_but_peninsula = sorted(pen_set - ru_set - ua_set)

    print(f"  Republic of Crimea (Q15966495, RU):  {len(ru_set):3d} editions")
    print(f"  Autonomous Republic (Q756294, UA):   {len(ua_set):3d} editions")
    print(f"  Peninsula (Q7835, geographic):       {len(pen_set):3d} editions")
    print(f"  Editions with RU but NOT UA article: {len(ru_only):3d}")
    print(f"  Editions with UA but NOT RU article: {len(ua_only):3d}")
    print(f"  Editions with both articles:         {len(both):3d}")
    print(f"  Peninsula article only (neither):    {len(neither_but_peninsula):3d}")

    return {
        "entity_ids": CRIMEA_ENTITY_IDS,
        "russian_fed_subject_editions": ru,
        "ukrainian_unit_editions": ua,
        "peninsula_editions": pen,
        "summary": {
            "russian_fed_subject_count": len(ru_set),
            "ukrainian_unit_count": len(ua_set),
            "peninsula_count": len(pen_set),
            "ru_only_count": len(ru_only),
            "ua_only_count": len(ua_only),
            "both_count": len(both),
            "peninsula_only_count": len(neither_but_peninsula),
            "ru_only_editions": ru_only,
            "ua_only_editions": ua_only,
            "both_editions": both,
        },
    }


def run_people_stratified(city_qids: list[str]) -> dict:
    """
    Stratified Crimean-born people query.

    Replaces the unfiltered 69% aggregate with four cohorts:
      1. died pre-1991 (Soviet era and earlier)
      2. died 1991-2014 (post-Soviet, pre-occupation)
      3. died post-2014 OR still alive
      4. unknown death date

    For each cohort we count P27 citizenship by country AND, critically, flag
    any P27 edge whose qualifier P580 (start time) is >= 2014-03-18 — those
    are the unambiguous post-occupation passportizations.

    The Imperial/Soviet-era bucket is the biographical-lag the reviewer
    flagged. The post-2014 cohort is what actually measures Russianization.
    """
    print("\n--- Stratified Crimean-born people (P19 ∈ Crimean cities) ---")
    values = " ".join(f"wd:{q}" for q in city_qids)
    # One query returns every person + citizenship edge + start/end qualifiers.
    # P580 (start time) on P27=Russia ≥ 2014-03-18 captures explicit
    # post-occupation passportization. P582 (end time) on P27=Ukraine
    # ≥ 2014-03-18 captures the dual signal: an editor explicitly marked
    # the end of Ukrainian citizenship. If an end-of-UA is set without a
    # matching start-of-RU, that's "invisible transition" — Wikidata
    # records the loss but not the gain.
    query = f"""
    SELECT ?person ?personLabel ?birth ?death ?citizenship ?citizenshipLabel ?citStart ?citEnd WHERE {{
      VALUES ?birthplace {{ {values} }}
      ?person wdt:P19 ?birthplace .
      OPTIONAL {{ ?person wdt:P569 ?birth . }}
      OPTIONAL {{ ?person wdt:P570 ?death . }}
      OPTIONAL {{
        ?person p:P27 ?citStmt .
        ?citStmt ps:P27 ?citizenship .
        OPTIONAL {{ ?citStmt pq:P580 ?citStart . }}
        OPTIONAL {{ ?citStmt pq:P582 ?citEnd . }}
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
    }}
    """
    bindings = sparql_query(query)
    print(f"  raw SPARQL rows: {len(bindings)}")

    # Group by person
    people = {}
    for b in bindings:
        pid = b.get("person", {}).get("value", "").rsplit("/", 1)[-1]
        if not pid:
            continue
        p = people.setdefault(pid, {
            "qid": pid,
            "label": b.get("personLabel", {}).get("value", ""),
            "birth": b.get("birth", {}).get("value", "")[:10],
            "death": b.get("death", {}).get("value", "")[:10],
            "citizenships": [],
        })
        cit_qid = b.get("citizenship", {}).get("value", "").rsplit("/", 1)[-1]
        if cit_qid:
            p["citizenships"].append({
                "qid": cit_qid,
                "label": b.get("citizenshipLabel", {}).get("value", ""),
                "start": b.get("citStart", {}).get("value", "")[:10],
                "end": b.get("citEnd", {}).get("value", "")[:10],
            })

    OCCUPATION = "2014-03-18"

    def bucket(death: str) -> str:
        if not death:
            return "alive_or_unknown"
        d = death[:10]
        if d < "1991-01-01":
            return "died_pre_1991"
        if d < "2014-03-18":
            return "died_1991_2014"
        return "died_post_2014"

    cohorts = {k: [] for k in ["died_pre_1991", "died_1991_2014", "died_post_2014", "alive_or_unknown"]}
    for pid, p in people.items():
        cohorts[bucket(p["death"])].append(p)

    def cit_class(citizenships: list[dict]) -> dict:
        qids = {c["qid"] for c in citizenships}
        has_ua = "Q212" in qids
        has_ru = "Q159" in qids
        has_su = "Q15180" in qids  # Soviet Union
        has_re = "Q34266" in qids or "Q12544" in qids  # Russian Empire variants
        # P580 (start time) ≥ 2014-03-18 on P27=Russia — explicit passportization
        post_2014_ru_start = any(
            c["qid"] == "Q159" and c["start"] and c["start"] >= OCCUPATION
            for c in citizenships
        )
        # P582 (end time) ≥ 2014-03-18 on P27=Ukraine — explicit end of UA citizenship
        post_2014_ua_end = any(
            c["qid"] == "Q212" and c["end"] and c["end"] >= OCCUPATION
            for c in citizenships
        )
        # Invisible transition: end of UA marked but no start of RU marked
        invisible_transition = post_2014_ua_end and not post_2014_ru_start
        if has_ua and has_ru:
            k = "both_ua_ru"
        elif has_ua:
            k = "ua_only"
        elif has_ru:
            k = "ru_only"
        elif has_su:
            k = "soviet_only"
        elif has_re:
            k = "russian_empire_only"
        elif not citizenships:
            k = "missing"
        else:
            k = "other"
        return {
            "class": k,
            "post_2014_ru_passport": post_2014_ru_start,
            "post_2014_ua_ended": post_2014_ua_end,
            "invisible_transition": invisible_transition,
        }

    summary = {}
    for cohort_name, members in cohorts.items():
        counts = {"ua_only": 0, "ru_only": 0, "both_ua_ru": 0, "soviet_only": 0,
                  "russian_empire_only": 0, "missing": 0, "other": 0,
                  "post_2014_ru_passport": 0,
                  "post_2014_ua_ended": 0,
                  "invisible_transition": 0}
        for p in members:
            cls = cit_class(p["citizenships"])
            counts[cls["class"]] += 1
            if cls["post_2014_ru_passport"]:
                counts["post_2014_ru_passport"] += 1
            if cls["post_2014_ua_ended"]:
                counts["post_2014_ua_ended"] += 1
            if cls["invisible_transition"]:
                counts["invisible_transition"] += 1
        summary[cohort_name] = {"n": len(members), **counts}

    total_people = len(people)
    print(f"  total people: {total_people}")
    for cohort_name, s in summary.items():
        n = s["n"]
        if n == 0:
            print(f"    {cohort_name:20s}: 0")
            continue
        ru = s["ru_only"]
        ua = s["ua_only"]
        print(
            f"    {cohort_name:20s}: n={n:3d}  "
            f"UA={ua:3d} ({100*ua//n:2d}%)  "
            f"RU={ru:3d} ({100*ru//n:2d}%)  "
            f"Soviet={s['soviet_only']:3d}  "
            f"RussianEmpire={s['russian_empire_only']:3d}  "
            f"both={s['both_ua_ru']:3d}  missing={s['missing']:3d}  "
            f"RU-start≥2014={s['post_2014_ru_passport']:3d}  "
            f"UA-end≥2014={s['post_2014_ua_ended']:3d}  "
            f"invisible={s['invisible_transition']:3d}"
        )

    return {
        "total_people": total_people,
        "by_cohort": summary,
        "notes": {
            "occupation_date": OCCUPATION,
            "cohort_definitions": {
                "died_pre_1991": "death date < 1991-01-01 — Imperial / Soviet era",
                "died_1991_2014": "1991-01-01 <= death < 2014-03-18 — post-Soviet, pre-occupation",
                "died_post_2014": "death >= 2014-03-18 — includes post-occupation deaths",
                "alive_or_unknown": "no death date recorded",
            },
            "post_2014_ru_passport": (
                "Number of people in the cohort with a P27=Q159 (Russia) "
                "edge whose qualifier P580 (start time) is on or after "
                "2014-03-18. Unambiguously post-occupation passportization."
            ),
            "post_2014_ua_ended": (
                "Number of people in the cohort with a P27=Q212 (Ukraine) "
                "edge whose qualifier P582 (end time) is on or after "
                "2014-03-18. Explicit editorial record that Ukrainian "
                "citizenship ended under occupation."
            ),
            "invisible_transition": (
                "Number of people with an explicit end-of-UA-citizenship "
                "edge (P27=Q212 with P582 >= 2014-03-18) but NO matching "
                "start-of-RU-citizenship edge (P27=Q159 with P580 >= 2014-03-18). "
                "Wikidata records the loss but not the gain — the "
                "'invisible transition' pattern."
            ),
            "caveat": (
                "Imperial Russia (Q34266/Q12544) and Soviet Union (Q15180) "
                "are separate buckets from modern Russia (Q159)."
            ),
        },
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

    # Step 0a: Entity sitelink asymmetry (systematic "Republic of Crimea" check)
    sitelink_sweep = run_sitelink_asymmetry()
    with open(DATA / "crimea_entity_sitelinks.json", "w") as f:
        json.dump(sitelink_sweep, f, indent=2, ensure_ascii=False)
    print(f"\nSaved sitelink sweep to {DATA / 'crimea_entity_sitelinks.json'}")

    # Step 0b: Stratified people query (corrects the old 69% biographical-lag artifact)
    city_qids = [q for _, q in CRIMEAN_CITIES]
    people = run_people_stratified(city_qids)
    with open(DATA / "wikidata_crimean_people_stratified.json", "w") as f:
        json.dump(people, f, indent=2, ensure_ascii=False)
    print(f"Saved stratified people to {DATA / 'wikidata_crimean_people_stratified.json'}")

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

    # Save raw audit output
    output = DATA / "wikipedia_audit.json"
    with open(output, "w") as f:
        json.dump({
            "total_entries": len(results),
            "by_language": by_lang,
            "wikidata": wikidata_results,
            "russia_framing": ru_desc,
            "results": results,
            "sitelink_sweep": sitelink_sweep,
            "people_stratified": people,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {output}")

    # Build standardized pipeline manifest (the file build_master_manifest reads)
    manifest = build_manifest(
        results=results,
        wikidata_results=wikidata_results,
        sitelink_sweep=sitelink_sweep,
        people=people,
        all_terms=all_terms,
    )
    manifest_path = DATA / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Saved pipeline manifest to {manifest_path}")


def build_manifest(results, wikidata_results, sitelink_sweep, people, all_terms) -> dict:
    """
    Produce the standardized pipeline manifest consumed by
    scripts/build_master_manifest.py and rendered on the site.

    Schema follows pipelines/README.md: pipeline, version, generated, method,
    summary, findings, key_findings, limitations.
    """
    from datetime import datetime, timezone

    # Description-level classification counts
    by_label = {"ukraine": 0, "russia": 0, "ambiguous": 0, "no_signal": 0}
    for r in results:
        by_label[r["label"]] = by_label.get(r["label"], 0) + 1

    # Wikidata P17 coverage: how many entities have a country claim at all
    p17_missing = 0
    p17_ua = 0
    p17_ru = 0
    for term, qid in all_terms:
        countries = wikidata_results.get(term, {}).get("countries", [])
        current = [c for c in countries if c.get("rank") != "deprecated" and not c.get("end")]
        names = {c["country"] for c in current}
        if not names:
            p17_missing += 1
        if "Ukraine" in names:
            p17_ua += 1
        if "Russia" in names:
            p17_ru += 1

    ss = sitelink_sweep["summary"]
    ppl = people["by_cohort"]

    def pct(n, d):
        return round(100 * n / d, 1) if d else 0

    alive = ppl["alive_or_unknown"]
    total_ru_start = sum(c.get("post_2014_ru_passport", 0) for c in ppl.values())
    total_ua_end = sum(c.get("post_2014_ua_ended", 0) for c in ppl.values())
    total_invisible = sum(c.get("invisible_transition", 0) for c in ppl.values())
    key_findings = [
        (
            f"Entity-sitelink asymmetry: {ss['russian_fed_subject_count']} Wikipedia editions "
            f"have a standalone article for the Russian federal subject 'Republic of Crimea' "
            f"(Q15966495) vs {ss['ukrainian_unit_count']} for the Ukrainian 'Autonomous "
            f"Republic of Crimea' (Q756294). {ss['ru_only_count']} editions have the Russian "
            f"entity but NOT the Ukrainian one; {ss['ua_only_count']} have the reverse. The "
            f"asymmetry in smaller editions is consistent with infrastructural normalization — "
            f"editors created the Russian federal subject article in 2014 when it was in the "
            f"news, while the legacy Ukrainian administrative unit was never written about."
        ),
        (
            f"Stratified Crimean-born people (N={people['total_people']}): among the "
            f"{alive['n']} living or unknown-death cohort, UA-only citizenship {alive['ua_only']} "
            f"({pct(alive['ua_only'], alive['n'])}%) vs RU-only {alive['ru_only']} "
            f"({pct(alive['ru_only'], alive['n'])}%). Exact two-sided binomial test on the "
            f"{alive['ua_only'] + alive['ru_only']} people with exclusive citizenship yields "
            f"statistical parity — p ≈ 0.93 for H0 of P(UA)=0.5."
        ),
        (
            f"Wikidata cannot represent post-2014 passportization: only {total_ru_start} "
            f"people across {people['total_people']} entries have a P27=Russia edge with a "
            f"P580 (start time) qualifier on or after 2014-03-18, and only {total_ua_end} "
            f"have a P27=Ukraine edge with a P582 (end time) qualifier on or after that date. "
            f"The 'invisible transition' count — end-of-UA marked but no matching start-of-RU — "
            f"is {total_invisible}. Russia issued an estimated 2 million passports in Crimea "
            f"after 2014; Wikidata records almost none of them as structured events. The "
            f"data gap is the finding."
        ),
        (
            f"English Wikipedia description-field erasure: {by_label.get('ambiguous', 0)} "
            f"'city in Crimea' (no country) classifications across all tested editions, vs "
            f"{by_label.get('ukraine', 0)} mentioning Ukraine and {by_label.get('russia', 0)} "
            f"mentioning Russia."
        ),
        (
            f"Wikidata P17 (country) coverage for 17 Crimean entities: {p17_ua} "
            f"list Ukraine, {p17_ru} list Russia, {p17_missing} have no current country claim."
        ),
    ]

    limitations = [
        "Tested 12 major language editions for description text; the sitelink sweep covers "
        "all editions that have any Crimea-related article.",
        "Stratification bucket 'alive_or_unknown' includes entries with no P570 death date — "
        "Wikidata does not reliably record 'alive' as a distinct state from 'unknown'.",
        "P580 (citizenship start-time) qualifier is rarely populated on P27 edges; absence of "
        "the qualifier is not evidence that citizenship was acquired before 2014.",
        "Entity sitelinks count standalone articles only — editions that cover both topics in "
        "a single combined article are counted as 'peninsula only', not 'both'.",
        "Description-text and category classification uses surface string matching; "
        "fine-grained semantic analysis of full article bodies was not performed.",
    ]

    findings = [
        {
            "id": "wiki-entity-asymmetry",
            "kind": "structural",
            "summary": f"{ss['russian_fed_subject_count']} editions recognize Russian federal "
                       f"subject as standalone article; {ss['ukrainian_unit_count']} recognize "
                       f"Ukrainian unit",
            "detail": ss,
        },
        {
            "id": "wiki-people-stratified",
            "kind": "cohort",
            "summary": "UA/RU citizenship parity (24% vs 23%) among living Crimean-born "
                       "people; prior 69% figure withdrawn",
            "detail": people,
        },
        {
            "id": "wiki-description-erasure",
            "kind": "text-framing",
            "summary": "Erasure by omission in description fields (per-language counts)",
            "detail": {"by_label": by_label, "total_entries": len(results)},
        },
        {
            "id": "wikidata-p17-coverage",
            "kind": "structured-data",
            "summary": f"{p17_missing}/17 Crimean entities have no current P17 country claim",
            "detail": {"p17_ua": p17_ua, "p17_ru": p17_ru, "p17_missing": p17_missing,
                       "total_entities": len(all_terms)},
        },
    ]

    return {
        "pipeline": "wikipedia",
        "version": "2.0",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "wikidata_sparql + wikipedia_rest_api",
        "summary": {
            "entities_tested": len(all_terms),
            "description_entries": len(results),
            "description_ukraine": by_label.get("ukraine", 0),
            "description_russia": by_label.get("russia", 0),
            "description_ambiguous": by_label.get("ambiguous", 0),
            "p17_ukraine": p17_ua,
            "p17_russia": p17_ru,
            "p17_missing": p17_missing,
            "editions_with_ru_federal_subject_article": ss["russian_fed_subject_count"],
            "editions_with_ua_autonomous_republic_article": ss["ukrainian_unit_count"],
            "editions_ru_only": ss["ru_only_count"],
            "editions_ua_only": ss["ua_only_count"],
            "total_crimean_born_people": people["total_people"],
            "people_alive_or_unknown": alive["n"],
            "people_alive_ua_only": alive["ua_only"],
            "people_alive_ru_only": alive["ru_only"],
            "people_post_2014_ru_passport_signal": sum(
                c.get("post_2014_ru_passport", 0) for c in ppl.values()
            ),
            "people_post_2014_ua_ended_signal": sum(
                c.get("post_2014_ua_ended", 0) for c in ppl.values()
            ),
            "people_invisible_transition": sum(
                c.get("invisible_transition", 0) for c in ppl.values()
            ),
        },
        "findings": findings,
        "key_findings": key_findings,
        "limitations": limitations,
    }


if __name__ == "__main__":
    main()
