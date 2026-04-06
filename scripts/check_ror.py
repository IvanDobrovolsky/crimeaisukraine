"""
ROR + OpenAlex institutional Crimea sovereignty audit.

Checks how global academic registries classify Crimean institutions.

Usage:
    python scripts/check_ror.py
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "data"
CONTACT = "dobrovolsky94@gmail.com"
HEADERS = {"User-Agent": f"CrimeaAudit/1.0 (mailto:{CONTACT})"}

CRIMEAN_CITIES = ["Crimea", "Simferopol", "Sevastopol", "Yalta", "Kerch",
                  "Feodosia", "Evpatoria", "Alushta", "Bakhchysarai"]


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error: {e}")
        return {}


def check_ror():
    """Query ROR v2 for Crimean institutions."""
    print("--- ROR (Research Organization Registry) ---")
    seen = set()
    results = []

    for city in CRIMEAN_CITIES:
        url = f"https://api.ror.org/v2/organizations?query={urllib.parse.quote(city)}"
        data = fetch_json(url)
        for item in data.get("items", []):
            ror_id = item.get("id", "")
            if ror_id in seen:
                continue
            seen.add(ror_id)

            # Get display name
            name = ""
            for n in item.get("names", []):
                if n.get("types") and "ror_display" in n["types"]:
                    name = n["value"]
                    break
            if not name and item.get("names"):
                name = item["names"][0].get("value", "")

            # Get location
            country = ""
            country_code = ""
            geo_city = ""
            for loc in item.get("locations", []):
                details = loc.get("geonames_details", {})
                country = details.get("country_name", "")
                country_code = details.get("country_code", "")
                geo_city = details.get("name", "")

            # Filter to Crimean institutions
            name_lower = name.lower()
            city_lower = geo_city.lower()
            is_crimean = any(c.lower() in name_lower or c.lower() in city_lower
                           for c in CRIMEAN_CITIES)
            if not is_crimean:
                continue

            status = item.get("status", "")
            results.append({
                "name": name,
                "ror_id": ror_id,
                "country": country,
                "country_code": country_code,
                "city": geo_city,
                "status": status,
            })
            flag = "UA" if country_code == "UA" else "RU" if country_code == "RU" else "?"
            print(f"  [{flag}] {name[:60]} | {geo_city} | {status}")

        time.sleep(0.3)

    return results


def check_openalex():
    """Query OpenAlex for Crimean institutions."""
    print("\n--- OpenAlex Institutions ---")
    seen = set()
    results = []

    for city in CRIMEAN_CITIES[:5]:  # Top cities
        url = (f"https://api.openalex.org/institutions?search={urllib.parse.quote(city)}"
               f"&per_page=15&mailto={CONTACT}")
        data = fetch_json(url)
        for inst in data.get("results", []):
            oa_id = inst.get("id", "")
            if oa_id in seen:
                continue
            seen.add(oa_id)

            name = inst.get("display_name", "")
            cc = inst.get("country_code", "")
            works = inst.get("works_count", 0)
            cited = inst.get("cited_by_count", 0)
            ror = inst.get("ror", "")
            geo = inst.get("geo", {})
            geo_city = geo.get("city", "")

            # Filter to Crimean
            is_crimean = any(c.lower() in name.lower() or c.lower() in geo_city.lower()
                           for c in CRIMEAN_CITIES)
            if not is_crimean:
                continue

            results.append({
                "name": name,
                "openalex_id": oa_id,
                "ror": ror,
                "country_code": cc,
                "city": geo_city,
                "works_count": works,
                "cited_by_count": cited,
            })
            print(f"  [{cc:2s}] {name[:55]:55s} | works={works:>6d} | cited={cited:>8d} | {geo_city}")

        time.sleep(0.3)

    return results


def main():
    print("ROR + OpenAlex Crimean Institution Audit")
    print("=" * 60)

    ror = check_ror()
    openalex = check_openalex()

    ua_ror = sum(1 for r in ror if r["country_code"] == "UA")
    ru_ror = sum(1 for r in ror if r["country_code"] == "RU")
    ua_oa = sum(1 for r in openalex if r["country_code"] == "UA")
    ru_oa = sum(1 for r in openalex if r["country_code"] == "RU")

    print(f"\nSummary:")
    print(f"  ROR: {len(ror)} institutions — UA={ua_ror}, RU={ru_ror}")
    print(f"  OpenAlex: {len(openalex)} institutions — UA={ua_oa}, RU={ru_oa}")

    output = {
        "source": "ROR + OpenAlex",
        "date": __import__("datetime").datetime.now().isoformat()[:10],
        "ror": {
            "total": len(ror),
            "ua": ua_ror,
            "ru": ru_ror,
            "institutions": ror,
        },
        "openalex": {
            "total": len(openalex),
            "ua": ua_oa,
            "ru": ru_oa,
            "institutions": openalex,
        },
        "finding": f"ROR classifies {ua_ror}/{len(ror)} Crimean institutions as Ukraine. "
                   f"But papers from these UA-registered institutions use 'Republic of Crimea, Russia' in metadata.",
    }

    out_path = DATA / "ror_institutions.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
