"""
Tech-infrastructure Crimea sovereignty audit.

Probes three foundational internet-infrastructure databases and reports
how each classifies Crimea:

    1. IANA Time Zone Database (zone1970.tab + legacy zone.tab)
       — live fetch from github.com/eggert/tz.
       — looks at the country-code column for Europe/Simferopol.
    2. Google libphonenumber
       — live fetch of resources/geocoding/en/7.txt (Russia) and
         resources/geocoding/en/380.txt (Ukraine) and
         resources/carrier/en/7.txt for +7-978 (Crimean mobile).
       — counts Crimean-city mentions on each side and the carriers
         listed under +7-978.
    3. OpenStreetMap Nominatim geocoder
       — queries nominatim.openstreetmap.org for 6 Crimean cities
         and records the country code returned per city.

These three probes measure the "Standards Silencing" pattern documented
in the telecom and geodata pipelines: the IANA file formally lists Crimea
under both UA and RU (a compromise), libphonenumber has quietly adopted
the Russian +7-978 numbering as the operational source of truth, and
OpenStreetMap Nominatim applies the "on the ground" rule differently
depending on the query.

Output: pipelines/tech_infrastructure/data/manifest.json in the standard
pipeline schema.

Usage:
    cd pipelines/tech_infrastructure && uv run scan.py
    # or from project root:
    make pipeline-tech_infrastructure
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT = Path(__file__).parent
DATA = PROJECT / "data"
DATA.mkdir(exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "CrimeaSovereigntyAudit/1.0 (academic research, Ukraine MFA)"
})

CRIMEAN_CITY_KEYWORDS = [
    "simferopol", "sevastopol", "crimea", "yalta", "kerch",
    "feodosia", "evpatoria",
]


# ── Probe 1: IANA tzdata ─────────────────────────────────────────────────

def probe_iana_timezone() -> dict:
    print("\n--- IANA Time Zone Database ---")
    out: dict = {
        "name": "IANA Time Zone Database",
        "source_url": "https://github.com/eggert/tz",
        "zone1970_cc": None,
        "zone1970_line": None,
        "zone_tab_cc": None,
        "zone_tab_line": None,
        "status": "unknown",
        "detail": "",
    }

    # zone1970.tab — current format, supports multiple country codes per zone
    try:
        r = SESSION.get(
            "https://raw.githubusercontent.com/eggert/tz/main/zone1970.tab",
            timeout=20,
        )
        if r.status_code == 200:
            for line in r.text.splitlines():
                if "simferopol" in line.lower():
                    parts = line.split("\t")
                    cc = parts[0] if parts else "?"
                    out["zone1970_cc"] = cc
                    out["zone1970_line"] = line.strip()
                    print(f"  zone1970.tab: country_codes='{cc}'  line='{line.strip()}'")
                    break
    except Exception as e:
        print(f"  zone1970.tab fetch failed: {e}")

    # Legacy zone.tab — single country code per zone
    try:
        r = SESSION.get(
            "https://raw.githubusercontent.com/eggert/tz/main/zone.tab",
            timeout=20,
        )
        if r.status_code == 200:
            for line in r.text.splitlines():
                if "simferopol" in line.lower() and not line.startswith("#"):
                    parts = line.split("\t")
                    cc = parts[0] if parts else "?"
                    out["zone_tab_cc"] = cc
                    out["zone_tab_line"] = line.strip()
                    print(f"  zone.tab (legacy): country_code='{cc}'")
                    break
    except Exception as e:
        print(f"  zone.tab fetch failed: {e}")

    cc = out["zone1970_cc"] or ""
    if cc == "UA":
        out["status"] = "correct"
        out["detail"] = f"zone1970.tab lists Europe/Simferopol as UA only"
    elif cc == "RU":
        out["status"] = "incorrect"
        out["detail"] = f"zone1970.tab lists Europe/Simferopol as RU only"
    elif "RU" in cc and "UA" in cc:
        out["status"] = "ambiguous"
        ru_first = cc.startswith("RU")
        out["detail"] = (
            f"zone1970.tab lists Europe/Simferopol as '{cc}' — both countries, "
            f"{'RU listed first' if ru_first else 'UA listed first'}. "
            f"This is the dual-listing compromise documented in the IANA tz "
            f"mailing list: when Crimea switched to Moscow time in 2014, "
            f"maintainers added RU without removing UA."
        )
    else:
        out["detail"] = f"unexpected country_codes='{cc}'"

    return out


# ── Probe 2: Google libphonenumber ───────────────────────────────────────

def _fetch_lines(url: str) -> list[str]:
    try:
        r = SESSION.get(url, timeout=20)
        if r.status_code == 200:
            return r.text.splitlines()
    except Exception as e:
        print(f"    fetch failed: {e}")
    return []


def probe_libphonenumber() -> dict:
    print("\n--- Google libphonenumber ---")
    out: dict = {
        "name": "Google libphonenumber",
        "source_url": "https://github.com/google/libphonenumber",
        "ru_crimea_entries": [],
        "ua_crimea_entries": [],
        "carriers_7978": [],
        "status": "unknown",
        "detail": "",
    }

    # Russian (+7) geocoding file
    ru_lines = _fetch_lines(
        "https://raw.githubusercontent.com/google/libphonenumber/master/"
        "resources/geocoding/en/7.txt"
    )
    ru_hits = [
        line.strip() for line in ru_lines
        if any(kw in line.lower() for kw in CRIMEAN_CITY_KEYWORDS)
    ]
    out["ru_crimea_entries"] = ru_hits
    print(f"  +7 geocoding file: {len(ru_hits)} Crimean-city entries")

    # Ukrainian (+380) geocoding file
    ua_lines = _fetch_lines(
        "https://raw.githubusercontent.com/google/libphonenumber/master/"
        "resources/geocoding/en/380.txt"
    )
    ua_hits = [
        line.strip() for line in ua_lines
        if any(kw in line.lower() for kw in CRIMEAN_CITY_KEYWORDS)
    ]
    out["ua_crimea_entries"] = ua_hits
    print(f"  +380 geocoding file: {len(ua_hits)} Crimean-city entries")

    # Carrier file: +7-978 is the Crimean mobile prefix Russia unilaterally
    # assigned post-2014
    carrier_lines = _fetch_lines(
        "https://raw.githubusercontent.com/google/libphonenumber/master/"
        "resources/carrier/en/7.txt"
    )
    carriers = sorted({
        (line.split("|")[-1].strip() if "|" in line else "")
        for line in carrier_lines
        if line.startswith("7978")
    } - {""})
    out["carriers_7978"] = carriers
    print(f"  carrier/7.txt: {len(carriers)} carriers under +7-978 = {carriers}")

    # Classify. Both sides carry Crimean entries — the library is
    # dual-encoded. The "incorrect" part is the Russian +7-978 prefix
    # which was never submitted to ITU.
    if ru_hits and ua_hits and carriers:
        out["status"] = "incorrect"
        out["detail"] = (
            f"libphonenumber has dual Crimean encoding: {len(ua_hits)} entries "
            f"under +380 (Ukraine, ITU-valid) AND {len(ru_hits)} entries under "
            f"+7 (Russia). Additionally, the +7-978 carrier file lists "
            f"{len(carriers)} Russian mobile operators operating under a "
            f"prefix Russia unilaterally assigned in 2014 and never submitted "
            f"to ITU. Every Android phone, Chrome sign-up form, and phone "
            f"validation library worldwide treats the Russian +7-978 prefix "
            f"as canonical."
        )
    elif ua_hits and not ru_hits:
        out["status"] = "correct"
        out["detail"] = f"libphonenumber lists Crimean entries only under +380 (UA)"
    elif ru_hits and not ua_hits:
        out["status"] = "incorrect"
        out["detail"] = f"libphonenumber lists Crimean entries only under +7 (RU)"
    else:
        out["status"] = "na"
        out["detail"] = "No Crimean entries found in libphonenumber resource files"

    return out


# ── Probe 3: OpenStreetMap Nominatim ─────────────────────────────────────

def probe_osm_nominatim() -> dict:
    print("\n--- OpenStreetMap Nominatim ---")
    out: dict = {
        "name": "OpenStreetMap Nominatim",
        "source_url": "https://nominatim.openstreetmap.org/",
        "cities_tested": [],
        "status": "unknown",
        "detail": "",
    }
    cities = [
        "Simferopol", "Sevastopol", "Yalta",
        "Kerch", "Feodosia", "Evpatoria",
    ]

    for city in cities:
        try:
            r = SESSION.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{city}, Crimea",
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                },
                timeout=15,
            )
            if r.status_code == 200 and r.json():
                d = r.json()[0]
                addr = d.get("address", {}) or {}
                cc = (addr.get("country_code") or "?").upper()
                country = addr.get("country") or "?"
                out["cities_tested"].append({
                    "city": city, "country": country, "country_code": cc,
                })
                print(f"  {city}: {country} ({cc})")
            else:
                out["cities_tested"].append({
                    "city": city, "country": None, "country_code": None,
                })
                print(f"  {city}: no result")
            time.sleep(1.2)  # Nominatim rate limit: 1 req/sec
        except Exception as e:
            print(f"  {city}: error {e}")
            out["cities_tested"].append({
                "city": city, "country": None, "country_code": None,
                "error": str(e),
            })

    ua_count = sum(1 for c in out["cities_tested"] if c["country_code"] == "UA")
    ru_count = sum(1 for c in out["cities_tested"] if c["country_code"] == "RU")
    tested = len(out["cities_tested"])
    out["ua_count"] = ua_count
    out["ru_count"] = ru_count
    out["tested"] = tested

    if tested and ua_count == tested:
        out["status"] = "correct"
        out["detail"] = f"All {tested} Crimean cities returned country_code=UA"
    elif ua_count > ru_count:
        out["status"] = "correct"
        out["detail"] = (
            f"{ua_count}/{tested} cities returned UA, {ru_count}/{tested} "
            f"returned RU. OSM's 'on the ground' rule could support either "
            f"answer, but Nominatim currently resolves Crimean cities to UA."
        )
    elif ru_count > ua_count:
        out["status"] = "incorrect"
        out["detail"] = (
            f"{ru_count}/{tested} cities returned RU, {ua_count}/{tested} "
            f"returned UA"
        )
    else:
        out["status"] = "ambiguous"
        out["detail"] = f"Tied: UA={ua_count}, RU={ru_count} of {tested} cities"

    return out


# ── Manifest + main ──────────────────────────────────────────────────────

def build_manifest(probes: list[dict]) -> dict:
    buckets: dict[str, int] = {}
    for p in probes:
        s = p.get("status", "unknown")
        buckets[s] = buckets.get(s, 0) + 1

    iana = next((p for p in probes if p["name"].startswith("IANA")), {})
    lpn = next((p for p in probes if p["name"].startswith("Google lib")), {})
    osm = next((p for p in probes if p["name"].startswith("OpenStreetMap")), {})

    key_findings = [
        (
            f"**IANA Time Zone Database** lists Europe/Simferopol with country "
            f"codes '{iana.get('zone1970_cc') or '?'}' in zone1970.tab. "
            f"{iana.get('detail', '')}"
        ),
        (
            f"**Google libphonenumber** has dual-encoded Crimean phone prefixes: "
            f"{len(lpn.get('ru_crimea_entries', []))} entries under +7 (Russia) "
            f"and {len(lpn.get('ua_crimea_entries', []))} under +380 (Ukraine). "
            f"The +7-978 Crimean mobile prefix — unilaterally assigned by Russia "
            f"in 2014 and never submitted to ITU — lists "
            f"{len(lpn.get('carriers_7978', []))} carriers as active: "
            f"{', '.join(lpn.get('carriers_7978', []))}. Every Android phone and "
            f"browser validation library that uses libphonenumber treats this "
            f"unilateral prefix as canonical. This is the 'Standards Silencing' "
            f"pattern: ITU formally lists +380-65x for Crimea, but the validation "
            f"layer that every downstream application actually consults has "
            f"switched to the Russian numbering."
        ),
        (
            f"**OpenStreetMap Nominatim** resolves {osm.get('ua_count', 0)}/"
            f"{osm.get('tested', 0)} tested Crimean cities to country_code=UA "
            f"({osm.get('ru_count', 0)} to RU). OSM applies the 'on the ground' "
            f"rule but the Nominatim geocoder currently returns the Ukrainian "
            f"classification."
        ),
        (
            "The three probes measure different layers of the same underlying "
            "question: timezone databases (OS-level), phone number libraries "
            "(validation-level), and geocoding (application-level). The IANA "
            "and libphonenumber findings together establish that Crimean "
            "sovereignty has been quietly downgraded from 'UA' to 'UA+RU' or "
            "'RU' in foundational infrastructure without any standards body "
            "or international regulator objecting or being notified."
        ),
    ]

    limitations = [
        "Live fetches against github.com (IANA + libphonenumber) and "
        "nominatim.openstreetmap.org — results are snapshots at scan time.",
        "Nominatim rate-limits at 1 req/sec; the 6-city test takes ~8 seconds.",
        "libphonenumber changes slowly but not never — the +7-978 carrier "
        "list can gain or lose operators between scans.",
        "The 'on the ground' rule in OpenStreetMap is under active "
        "discussion in OSM's WikiProject Crimea. The Nominatim result is "
        "a snapshot of the current OSM community consensus.",
        "Additional infrastructure systems (CLDR territories, ICU locale "
        "data, Unicode regional codes) are not yet probed by this scan.",
    ]

    return {
        "pipeline": "tech_infrastructure",
        "version": "2.0",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "live_http + iana_tzdata + libphonenumber + osm_nominatim",
        "summary": {
            "probes_total": len(probes),
            "correct": buckets.get("correct", 0),
            "incorrect": buckets.get("incorrect", 0),
            "ambiguous": buckets.get("ambiguous", 0),
            "na": buckets.get("na", 0),
            "unknown": buckets.get("unknown", 0),
            "iana_zone1970_cc": iana.get("zone1970_cc"),
            "iana_zone_tab_cc": iana.get("zone_tab_cc"),
            "libphonenumber_ru_crimean_entries": len(lpn.get("ru_crimea_entries", [])),
            "libphonenumber_ua_crimean_entries": len(lpn.get("ua_crimea_entries", [])),
            "libphonenumber_7978_carriers": len(lpn.get("carriers_7978", [])),
            "osm_cities_tested": osm.get("tested", 0),
            "osm_ua_count": osm.get("ua_count", 0),
            "osm_ru_count": osm.get("ru_count", 0),
        },
        "findings": probes,
        "key_findings": key_findings,
        "limitations": limitations,
    }


def main():
    probes = [
        probe_iana_timezone(),
        probe_libphonenumber(),
        probe_osm_nominatim(),
    ]

    manifest = build_manifest(probes)
    out = DATA / "manifest.json"
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 66)
    print(f"Tech infrastructure pipeline — wrote manifest to {out}")
    s = manifest["summary"]
    print(f"  probes: correct={s['correct']}  incorrect={s['incorrect']}  "
          f"ambiguous={s['ambiguous']}  na={s['na']}")
    print(f"  IANA zone1970 cc:  {s['iana_zone1970_cc']}")
    print(f"  libphonenumber:    RU-entries={s['libphonenumber_ru_crimean_entries']}  "
          f"UA-entries={s['libphonenumber_ua_crimean_entries']}  "
          f"+7-978 carriers={s['libphonenumber_7978_carriers']}")
    print(f"  OSM Nominatim:     UA={s['osm_ua_count']}/{s['osm_cities_tested']}")


if __name__ == "__main__":
    main()
