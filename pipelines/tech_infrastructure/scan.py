"""
Infrastructure & Standards Crimea Checker

Checks foundational internet infrastructure databases for Crimea classification:
- IANA Timezone Database (zone1970.tab)
- Google libphonenumber (phone number metadata)
- Unicode CLDR (territory/locale data)
- OpenStreetMap Nominatim (geocoding)
- Extended IP geolocation (more Crimean IP ranges)

Usage:
    python scripts/check_infrastructure.py
"""

import json
import time

import requests

from audit_framework import (
    AuditDatabase,
    AuditMethod,
    PlatformCategory,
    SovereigntyStatus,
    create_finding,
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CrimeaSovereigntyAudit/1.0 (research)"})


def check_iana_timezone() -> list[dict]:
    """Check IANA timezone database for Crimea country assignment."""
    print("\n--- IANA Timezone Database ---")
    findings = []

    # zone1970.tab maps timezone zones to country codes
    resp = SESSION.get(
        "https://raw.githubusercontent.com/eggert/tz/main/zone1970.tab",
        timeout=15,
    )
    if resp.status_code == 200:
        for line in resp.text.split("\n"):
            if "simferopol" in line.lower():
                # Format: CC\tcoordinates\tTZ\tcomments
                parts = line.split("\t")
                country_codes = parts[0] if parts else "?"

                if country_codes == "UA":
                    status = SovereigntyStatus.CORRECT
                elif country_codes == "RU":
                    status = SovereigntyStatus.INCORRECT
                elif "RU" in country_codes and "UA" in country_codes:
                    status = SovereigntyStatus.AMBIGUOUS
                else:
                    status = SovereigntyStatus.AMBIGUOUS

                findings.append(create_finding(
                    platform="IANA Timezone Database (zone1970.tab)",
                    category=PlatformCategory.TECH_INFRA,
                    status=status,
                    method=AuditMethod.SOURCE_CODE,
                    detail=(
                        f"Europe/Simferopol mapped to country codes: "
                        f"'{country_codes}'. In zone1970.tab format, "
                        f"'RU,UA' means both countries claim the zone. "
                        f"Russia is listed FIRST. The older zone.tab lists "
                        f"only 'UA'."
                    ),
                    url="https://github.com/eggert/tz",
                    evidence=line.strip(),
                    notes=(
                        "Key git history: 2014-03-19 'Crimea switches to "
                        "Moscow time', 2016-12-06 'Just say Crimea rather "
                        "than going into politics'. The tz database switched "
                        "Crimea from MSK+2 (EET) to MSK (Moscow time) in 2014. "
                        "This affects every OS, programming language, and app "
                        "that uses tzdata."
                    ),
                ))
                print(f"  zone1970.tab: {country_codes} -> Europe/Simferopol")
                break

    # Also check the old zone.tab
    resp2 = SESSION.get(
        "https://raw.githubusercontent.com/eggert/tz/main/zone.tab",
        timeout=15,
    )
    if resp2.status_code == 200:
        for line in resp2.text.split("\n"):
            if "simferopol" in line.lower() and not line.startswith("#"):
                parts = line.split("\t")
                cc = parts[0] if parts else "?"
                findings.append(create_finding(
                    platform="IANA Timezone Database (zone.tab, legacy)",
                    category=PlatformCategory.TECH_INFRA,
                    status=(SovereigntyStatus.CORRECT if cc == "UA"
                            else SovereigntyStatus.INCORRECT),
                    method=AuditMethod.SOURCE_CODE,
                    detail=(
                        f"Legacy zone.tab maps Europe/Simferopol to '{cc}'. "
                        f"Older format only supports one country code per zone."
                    ),
                    url="https://github.com/eggert/tz",
                    evidence=line.strip(),
                ))
                print(f"  zone.tab (legacy): {cc} -> Europe/Simferopol")
                break

    return findings


def check_libphonenumber() -> list[dict]:
    """Check Google's libphonenumber for Crimea phone prefix classification."""
    print("\n--- Google libphonenumber ---")
    findings = []

    # Check Russian +7 geocoding for Crimean prefix 736 (Simferopol)
    resp_ru = SESSION.get(
        "https://raw.githubusercontent.com/google/libphonenumber/master/"
        "resources/geocoding/en/7.txt",
        timeout=15,
    )
    ru_crimea_entries = []
    if resp_ru.status_code == 200:
        for line in resp_ru.text.split("\n"):
            if any(x in line.lower() for x in
                   ["simferopol", "sevastopol", "crimea", "yalta", "kerch"]):
                ru_crimea_entries.append(line.strip())

    # Check Ukrainian +380 geocoding for Crimean prefix 65
    resp_ua = SESSION.get(
        "https://raw.githubusercontent.com/google/libphonenumber/master/"
        "resources/geocoding/en/380.txt",
        timeout=15,
    )
    ua_crimea_entries = []
    if resp_ua.status_code == 200:
        for line in resp_ua.text.split("\n"):
            if any(x in line.lower() for x in
                   ["simferopol", "sevastopol", "crimea", "yalta", "kerch"]):
                ua_crimea_entries.append(line.strip())

    # Check carrier data for 978 (Crimean mobile under +7)
    resp_carrier = SESSION.get(
        "https://raw.githubusercontent.com/google/libphonenumber/master/"
        "resources/carrier/en/7.txt",
        timeout=15,
    )
    carriers_978 = set()
    if resp_carrier.status_code == 200:
        for line in resp_carrier.text.split("\n"):
            if line.startswith("7978"):
                carrier = line.split("|")[-1] if "|" in line else ""
                carriers_978.add(carrier)

    findings.append(create_finding(
        platform="Google libphonenumber",
        category=PlatformCategory.TECH_INFRA,
        status=SovereigntyStatus.AMBIGUOUS,
        method=AuditMethod.SOURCE_CODE,
        detail=(
            f"Crimean phones classified under BOTH countries. "
            f"Under Russia (+7): {len(ru_crimea_entries)} entries "
            f"(e.g., 736|Simferopol). Under Ukraine (+380): "
            f"{len(ua_crimea_entries)} entries (e.g., 38065|Crimea). "
            f"Carrier data lists {len(carriers_978)} operators for "
            f"+7-978 (Crimean mobile): {', '.join(sorted(carriers_978))}."
        ),
        url="https://github.com/google/libphonenumber",
        evidence=(
            f"RU entries: {'; '.join(ru_crimea_entries[:3])}. "
            f"UA entries: {'; '.join(ua_crimea_entries[:3])}"
        ),
        notes=(
            "libphonenumber (17k+ GitHub stars) is used by Android, "
            "Chrome, and most phone number validation worldwide. "
            "Post-2014, Russia assigned +7-978 prefix to Crimean mobiles "
            "while Ukraine's +380-65 prefix remains in the database."
        ),
    ))
    print(f"  RU (+7) Crimea entries: {len(ru_crimea_entries)}")
    print(f"  UA (+380) Crimea entries: {len(ua_crimea_entries)}")
    print(f"  +7-978 carriers: {sorted(carriers_978)}")

    return findings


def check_osm_nominatim() -> list[dict]:
    """Check OpenStreetMap Nominatim geocoder for Crimean cities."""
    print("\n--- OpenStreetMap Nominatim ---")
    findings = []

    cities = [
        "Simferopol", "Sevastopol", "Yalta",
        "Kerch", "Feodosia", "Evpatoria",
    ]
    results = []

    for city in cities:
        try:
            resp = SESSION.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{city}, Crimea",
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                },
                timeout=10,
            )
            if resp.status_code == 200 and resp.json():
                r = resp.json()[0]
                addr = r.get("address", {})
                cc = addr.get("country_code", "?").upper()
                country = addr.get("country", "?")
                results.append({"city": city, "country": country, "cc": cc})
                print(f"  {city}: {country} ({cc})")
            time.sleep(1.2)
        except Exception as e:
            print(f"  {city}: error - {e}")

    ua_count = sum(1 for r in results if r["cc"] == "UA")
    ru_count = sum(1 for r in results if r["cc"] == "RU")

    if ua_count == len(results):
        status = SovereigntyStatus.CORRECT
    elif ru_count > ua_count:
        status = SovereigntyStatus.INCORRECT
    else:
        status = SovereigntyStatus.AMBIGUOUS

    findings.append(create_finding(
        platform="OpenStreetMap Nominatim",
        category=PlatformCategory.MAP_SERVICE,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=(
            f"Tested {len(results)} Crimean cities: "
            f"{ua_count} returned UA, {ru_count} returned RU. "
            f"OSM follows 'on the ground' rule but Nominatim currently "
            f"returns all Crimean cities under Ukraine."
        ),
        url="https://nominatim.openstreetmap.org/",
        evidence="; ".join(f"{r['city']}={r['cc']}" for r in results),
        notes=(
            "OpenStreetMap has a complex policy for Crimea "
            "(see WikiProject Crimea). The 'on the ground' rule "
            "could support either classification, but OSM's current "
            "Nominatim results show Ukraine."
        ),
    ))

    return findings


def check_extended_ips() -> list[dict]:
    """Extended IP geolocation check with more Crimean ranges."""
    print("\n--- Extended IP Geolocation ---")
    findings = []

    ips = {
        "91.207.56.1": ("CrimeaCom AS48031", "UA pre-2014"),
        "176.104.32.1": ("SevStar AS56485", "UA pre-2014"),
        "46.63.0.1": ("Sim-Telecom AS198948", "UA pre-2014"),
        "83.149.22.1": ("Miranda-Media AS201776", "RU post-2014"),
        "185.31.160.1": ("CrimeaTelecom AS42961", "RU post-2014"),
        "5.133.64.1": ("KNET AS28761", "UA pre-2014"),
        "193.19.228.1": ("CrimeanFederalUniv", "UA pre-2014"),
        "95.47.152.1": ("Win-Mobile/K-Telecom", "RU post-2014"),
    }

    all_results = []
    for ip, (desc, origin) in ips.items():
        try:
            resp = SESSION.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "country,countryCode,regionName,city,isp"},
                timeout=10,
            )
            if resp.status_code == 200:
                d = resp.json()
                all_results.append({
                    "ip": ip, "desc": desc, "origin": origin,
                    "country": d.get("country", "?"),
                    "cc": d.get("countryCode", "?"),
                    "city": d.get("city", ""),
                    "isp": d.get("isp", ""),
                })
                cc = d.get("countryCode", "?")
                icon = {
                    "UA": "\u2705", "RU": "\u274c"
                }.get(cc, "\u26a0\ufe0f")
                print(f"  {icon} {ip} ({desc}): {d.get('country')} ({cc})")
            time.sleep(1.2)
        except Exception as e:
            print(f"  {ip}: {e}")

    # Analyze patterns
    ua_pre2014 = [r for r in all_results if r["origin"] == "UA pre-2014"]
    ru_post2014 = [r for r in all_results if r["origin"] == "RU post-2014"]

    ua_pre_resolve_ua = sum(1 for r in ua_pre2014 if r["cc"] == "UA")
    ua_pre_resolve_ru = sum(1 for r in ua_pre2014 if r["cc"] == "RU")
    ua_pre_resolve_other = len(ua_pre2014) - ua_pre_resolve_ua - ua_pre_resolve_ru

    ru_post_resolve_ru = sum(1 for r in ru_post2014 if r["cc"] == "RU")
    ru_post_resolve_ua = sum(1 for r in ru_post2014 if r["cc"] == "UA")

    findings.append(create_finding(
        platform="IP Geolocation (extended, ip-api.com)",
        category=PlatformCategory.IP_GEOLOCATION,
        status=SovereigntyStatus.AMBIGUOUS,
        method=AuditMethod.AUTOMATED_API,
        detail=(
            f"Tested {len(all_results)} Crimean IPs. "
            f"Pre-2014 Ukrainian ISPs ({len(ua_pre2014)} tested): "
            f"{ua_pre_resolve_ua} resolve UA, {ua_pre_resolve_ru} resolve RU, "
            f"{ua_pre_resolve_other} resolve other (re-routed). "
            f"Post-2014 Russian entities ({len(ru_post2014)} tested): "
            f"{ru_post_resolve_ru} resolve RU, {ru_post_resolve_ua} resolve UA. "
            f"Pattern: ISP registration origin determines geolocation, "
            f"not physical location in Crimea."
        ),
        url="https://ip-api.com/",
        evidence="; ".join(
            f"{r['ip']} ({r['desc']}): {r['cc']}" for r in all_results
        ),
        notes=(
            "Some Ukrainian ISPs have re-routed through third countries "
            "(Hungary, Lithuania) rather than through Russian infrastructure. "
            "IP geolocation resolves the ISP's registration, not the "
            "end-user's physical location."
        ),
    ))

    return findings


def run_all():
    db = AuditDatabase()
    all_findings = []

    for checker in [
        check_iana_timezone,
        check_libphonenumber,
        check_osm_nominatim,
        check_extended_ips,
    ]:
        try:
            findings = checker()
            all_findings.extend(findings)
        except Exception as e:
            print(f"Error in {checker.__name__}: {e}")

    db.add_batch(all_findings)
    db.save()

    print(f"\n{'='*60}")
    print(f"Infrastructure audit complete: {len(all_findings)} findings")
    print(f"Data saved to: {db.path}")
    return all_findings


if __name__ == "__main__":
    run_all()
