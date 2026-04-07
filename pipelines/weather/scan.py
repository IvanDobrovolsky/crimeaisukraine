"""
Platform Sovereignty Checker

Automated checks for web platforms (travel, weather, search, reference)
to determine how they classify Crimean locations.

Some checks require manual verification — this script documents what to
check and records findings from both automated and manual audits.

Usage:
    python scripts/check_platforms.py
"""

import json
import re
import time

import requests
from bs4 import BeautifulSoup

from audit_framework import (
    AuditDatabase,
    AuditMethod,
    PlatformCategory,
    SovereigntyStatus,
    create_finding,
)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
})


def check_wikipedia_crimea() -> list[dict]:
    """Check how Wikipedia describes Crimea across languages."""
    print("\n--- Checking Wikipedia ---")
    findings = []

    # Check English Wikipedia infobox via API
    langs = {
        "en": "English",
        "de": "German",
        "fr": "French",
        "it": "Italian",
        "es": "Spanish",
    }

    for lang, label in langs.items():
        url = (
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/Crimea"
        )
        try:
            resp = SESSION.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract", "")
                extract_lower = extract.lower()

                # Analyze the extract for sovereignty framing
                mentions_ukraine = any(w in extract_lower for w in
                    ["ukraine", "ukrainian", "україна"])
                mentions_russia = any(w in extract_lower for w in
                    ["russia", "russian", "россия", "annexed", "annexation"])
                mentions_occupied = "occupied" in extract_lower
                mentions_disputed = "disputed" in extract_lower

                if mentions_occupied or (mentions_ukraine and not mentions_russia):
                    status = SovereigntyStatus.CORRECT
                    framing = "frames as Ukrainian/occupied"
                elif mentions_ukraine and mentions_russia:
                    status = SovereigntyStatus.AMBIGUOUS
                    framing = "mentions both Ukraine and Russia"
                elif mentions_russia and not mentions_ukraine:
                    status = SovereigntyStatus.INCORRECT
                    framing = "frames as Russian without Ukrainian context"
                else:
                    status = SovereigntyStatus.AMBIGUOUS
                    framing = "unclear framing"

                findings.append(create_finding(
                    platform=f"Wikipedia ({label})",
                    category=PlatformCategory.REFERENCE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Article summary {framing}.",
                    url=f"https://{lang}.wikipedia.org/wiki/Crimea",
                    evidence=extract[:300],
                ))
                print(f"  {label}: {framing}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  {label}: error - {e}")

    return findings


def check_weather_services() -> list[dict]:
    """Check weather services for Simferopol country classification."""
    print("\n--- Checking Weather Services ---")
    findings = []

    # OpenWeatherMap (free API, returns country code)
    # Using their geocoding API
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": "Simferopol", "limit": 5}
    # Note: needs API key for full access, but geocoding endpoint
    # sometimes works without one for basic queries

    # AccuWeather search (public search endpoint)
    try:
        resp = SESSION.get(
            "https://www.accuweather.com/web-api/three-day-redirect",
            params={"query": "Simferopol"},
            timeout=15,
            allow_redirects=False,
        )
        location = resp.headers.get("Location", "")
        if location:
            if "/ua/" in location.lower():
                status = SovereigntyStatus.CORRECT
                detail = "Simferopol redirects to Ukraine country path"
            elif "/ru/" in location.lower():
                status = SovereigntyStatus.INCORRECT
                detail = "Simferopol redirects to Russia country path"
            else:
                status = SovereigntyStatus.AMBIGUOUS
                detail = f"Simferopol redirect path: {location}"

            findings.append(create_finding(
                platform="AccuWeather",
                category=PlatformCategory.WEATHER,
                status=status,
                method=AuditMethod.AUTOMATED_API,
                detail=detail,
                url="https://www.accuweather.com/",
                evidence=f"Redirect: {location}",
            ))
            print(f"  AccuWeather: {detail}")
    except Exception as e:
        print(f"  AccuWeather: error - {e}")

    return findings


def check_search_engines() -> list[dict]:
    """Check search engine knowledge panels for Crimea."""
    print("\n--- Checking Search Engines (manual verification needed) ---")
    findings = []

    # These need manual checking but we document what to look for
    manual_checks = [
        {
            "platform": "Google Search",
            "category": PlatformCategory.SEARCH_ENGINE,
            "url": "https://www.google.com/search?q=Crimea",
            "instructions": (
                "Search 'Crimea' on Google. Check the knowledge panel on the "
                "right side. Does it say 'Country: Ukraine' or 'Country: Russia'? "
                "Also check from different country VPNs (US, UK, Germany, Russia)."
            ),
        },
        {
            "platform": "Bing Search",
            "category": PlatformCategory.SEARCH_ENGINE,
            "url": "https://www.bing.com/search?q=Crimea",
            "instructions": (
                "Search 'Crimea' on Bing. Check the knowledge panel. "
                "What country does it show?"
            ),
        },
        {
            "platform": "DuckDuckGo",
            "category": PlatformCategory.SEARCH_ENGINE,
            "url": "https://duckduckgo.com/?q=Crimea",
            "instructions": (
                "Search 'Crimea' on DuckDuckGo. Check the instant answer box."
            ),
        },
    ]

    for check in manual_checks:
        findings.append(create_finding(
            platform=check["platform"],
            category=check["category"],
            status=SovereigntyStatus.AMBIGUOUS,  # Placeholder until manual check
            method=AuditMethod.MANUAL,
            detail=f"NEEDS MANUAL CHECK: {check['instructions']}",
            url=check["url"],
            notes="Placeholder — update after manual verification.",
        ))
        print(f"  {check['platform']}: needs manual check")

    return findings


def check_travel_platforms() -> list[dict]:
    """Check travel platforms for Crimea country classification."""
    print("\n--- Checking Travel Platforms ---")
    findings = []

    # Skyscanner API — check SIP (Simferopol) airport
    try:
        resp = SESSION.get(
            "https://www.skyscanner.com/transport/flights/sip/",
            timeout=15,
            allow_redirects=True,
        )
        if resp.status_code == 200:
            content = resp.text.lower()
            if "ukraine" in content:
                status = SovereigntyStatus.CORRECT
                detail = "SIP airport page mentions Ukraine"
            elif "russia" in content:
                status = SovereigntyStatus.INCORRECT
                detail = "SIP airport page mentions Russia"
            else:
                status = SovereigntyStatus.AMBIGUOUS
                detail = "SIP airport page — country unclear from HTML"

            findings.append(create_finding(
                platform="Skyscanner",
                category=PlatformCategory.TRAVEL,
                status=status,
                method=AuditMethod.AUTOMATED_API,
                detail=detail,
                url="https://www.skyscanner.com/transport/flights/sip/",
                notes="SIP = Simferopol International Airport (IATA code).",
            ))
            print(f"  Skyscanner: {detail}")
    except Exception as e:
        print(f"  Skyscanner: error - {e}")

    # Manual checks for platforms that need browser interaction
    manual_travel = [
        ("Booking.com", "https://www.booking.com/searchresults.html?ss=Simferopol",
         "Search Simferopol — check country label on results"),
        ("Airbnb", "https://www.airbnb.com/s/Simferopol/homes",
         "Search Simferopol — what country appears?"),
        ("Google Flights", "https://www.google.com/travel/flights",
         "Search flights to SIP — what country is listed?"),
        ("TripAdvisor", "https://www.tripadvisor.com/Search?q=simferopol",
         "Search Simferopol — check country in breadcrumb"),
    ]

    for name, url, instructions in manual_travel:
        findings.append(create_finding(
            platform=name,
            category=PlatformCategory.TRAVEL,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=f"NEEDS MANUAL CHECK: {instructions}",
            url=url,
            notes="Placeholder — update after manual verification.",
        ))
        print(f"  {name}: needs manual check")

    return findings


def check_gaming_platforms() -> list[dict]:
    """Document gaming platform checks (mostly manual)."""
    print("\n--- Documenting Gaming Platform Checks ---")
    findings = []

    manual_gaming = [
        ("Steam", PlatformCategory.GAMING,
         "https://store.steampowered.com/",
         "Check country/region settings. Steam blocks Crimea under US sanctions. "
         "Verify store region list — is Crimea listed separately?"),
        ("Epic Games Store", PlatformCategory.GAMING,
         "https://store.epicgames.com/",
         "Check region restrictions. Known to block Crimea."),
        ("EA Sports FC / FIFA", PlatformCategory.GAMING,
         "https://www.ea.com/games/ea-sports-fc",
         "Check player nationalities for Crimean-born players. "
         "Are they listed as Ukrainian or Russian?"),
        ("Hearts of Iron IV", PlatformCategory.GAMING,
         "https://store.steampowered.com/app/394360/Hearts_of_Iron_IV/",
         "Check map data files — how is Crimea's state/province defined?"),
    ]

    for name, category, url, instructions in manual_gaming:
        findings.append(create_finding(
            platform=name,
            category=category,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=f"NEEDS MANUAL CHECK: {instructions}",
            url=url,
            notes="Placeholder — update after manual verification.",
        ))
        print(f"  {name}: needs manual check")

    return findings


def run_all_platform_checks():
    """Run all platform checks."""
    db = AuditDatabase()
    all_findings = []

    checkers = [
        check_wikipedia_crimea,
        check_weather_services,
        check_search_engines,
        check_travel_platforms,
        check_gaming_platforms,
    ]

    for checker in checkers:
        try:
            findings = checker()
            all_findings.extend(findings)
        except Exception as e:
            print(f"Error in {checker.__name__}: {e}")

    db.add_batch(all_findings)
    db.save()

    print(f"\n{'='*60}")
    print(f"Platform audit complete: {len(all_findings)} findings")
    print(f"  Automated: {sum(1 for f in all_findings if f['method'] != 'manual')}")
    print(f"  Need manual check: {sum(1 for f in all_findings if f['method'] == 'manual')}")
    print(f"Data saved to: {db.path}")

    return all_findings


if __name__ == "__main__":
    run_all_platform_checks()
