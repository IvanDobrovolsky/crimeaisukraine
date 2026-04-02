"""
Semi-manual Playwright testing.

Opens each platform, waits for you to solve CAPTCHAs / dismiss popups,
then captures the result automatically. The infrastructure (screenshot,
signal extraction, classification) is automated; only CAPTCHA solving
is manual.

Method classification: "semi_automated" — programmatic data capture
with human-assisted anti-bot bypass.

Usage:
    python scripts/check_semi_manual.py
    python scripts/check_semi_manual.py --proxy socks5://127.0.0.1:1080 --label DE
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

from audit_framework import (
    AuditDatabase, AuditMethod, PlatformCategory,
    SovereigntyStatus, create_finding, DATA_DIR,
)

SCREENSHOT_DIR = DATA_DIR / "screenshots" / "semi_manual"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_FILE = DATA_DIR / "semi_manual_results.json"

WAIT_SECONDS = 20  # Time for human to solve CAPTCHA


def extract_signals(page):
    """Extract sovereignty signals from current page."""
    content = page.content().lower()
    url = page.url.lower()
    title = page.title().lower()
    return {
        "url": page.url,
        "title": page.title(),
        "has_ukraine_text": "ukraine" in content or "україна" in content,
        "has_russia_text": "russia" in content or "россия" in content,
        "has_annexed": "annex" in content,
        "has_occupied": "occupied" in content or "occupation" in content,
        "has_disputed": "disputed" in content,
        "url_has_ua": "/ua/" in url or "ukraine" in url,
        "url_has_ru": "/ru/" in url and "forum" not in url and "true" not in url,
    }


# Each entry: (name, category, url, what_to_look_for)
PLATFORMS = [
    # SEARCH ENGINES
    ("Google Search - Crimea", PlatformCategory.SEARCH_ENGINE,
     "https://www.google.com/search?q=Crimea&hl=en",
     "Check knowledge panel on right — does it show a country?"),
    ("Google Search - Simferopol", PlatformCategory.SEARCH_ENGINE,
     "https://www.google.com/search?q=Simferopol&hl=en",
     "Check knowledge panel — country field"),
    ("Yandex Search", PlatformCategory.SEARCH_ENGINE,
     "https://yandex.com/search/?text=Crimea",
     "Check results and knowledge panel"),
    ("Baidu Search", PlatformCategory.SEARCH_ENGINE,
     "https://www.baidu.com/s?wd=Crimea",
     "Chinese search — how does it frame Crimea?"),

    # MAPS
    ("Google Maps - Crimea zoom", PlatformCategory.MAP_SERVICE,
     "https://www.google.com/maps/@45.3,34.5,8z",
     "Check border rendering — solid, dashed, or absent?"),
    ("Google Maps - Simferopol", PlatformCategory.MAP_SERVICE,
     "https://www.google.com/maps/place/Simferopol",
     "Check what country label appears for Simferopol"),
    ("Apple Maps web", PlatformCategory.MAP_SERVICE,
     "https://maps.apple.com/?q=Simferopol",
     "Check country label"),

    # SOCIAL MEDIA — location tags
    ("Instagram - Simferopol", PlatformCategory.SOCIAL_MEDIA,
     "https://www.instagram.com/explore/locations/213225837/simferopol/",
     "Check location page — what country?"),
    ("Instagram - Crimea", PlatformCategory.SOCIAL_MEDIA,
     "https://www.instagram.com/explore/tags/crimea/",
     "Check tag page — any country context?"),
    ("TikTok - Crimea", PlatformCategory.SOCIAL_MEDIA,
     "https://www.tiktok.com/tag/crimea",
     "Check tag page"),
    ("Facebook - Simferopol", PlatformCategory.SOCIAL_MEDIA,
     "https://www.facebook.com/pages/category/City/Simferopol-108198449210498/",
     "Check city page — what country?"),

    # SPORTS
    ("FIFA - Crimea clubs", PlatformCategory.SPORTS,
     "https://www.fifa.com/en/search?q=simferopol",
     "Search for Simferopol — what country do results show?"),
    ("UEFA - Crimea", PlatformCategory.SPORTS,
     "https://www.uefa.com/uefachampionsleague/clubs/?q=crimea",
     "Any Crimean clubs and under which country?"),
    ("ESPN - Crimea", PlatformCategory.SPORTS,
     "https://www.espn.com/search/_/q/crimea",
     "Search results framing"),
    ("Olympics - Crimea athletes", PlatformCategory.SPORTS,
     "https://olympics.com/en/search?q=crimea",
     "How are Crimean athletes classified?"),

    # MEDIA — test for double game
    ("Reuters - Crimea", PlatformCategory.REFERENCE,
     "https://www.reuters.com/search/news?query=crimea",
     "Check framing — annexed? Russian?"),
    ("Al Jazeera - Crimea", PlatformCategory.REFERENCE,
     "https://www.aljazeera.com/search/crimea",
     "Check framing across articles"),
    ("BBC - Crimea", PlatformCategory.REFERENCE,
     "https://www.bbc.com/search?q=crimea",
     "Check framing"),
    ("CNN - Crimea", PlatformCategory.REFERENCE,
     "https://edition.cnn.com/search?q=crimea",
     "Check framing"),
    ("France24 - Crimea", PlatformCategory.REFERENCE,
     "https://www.france24.com/en/search?query=crimea",
     "French state media — check framing"),
    ("DW - Crimea", PlatformCategory.REFERENCE,
     "https://www.dw.com/search/?searchNavigationId=9077&languageCode=en&origin=gN&item=crimea",
     "German public broadcaster — check framing"),

    # TRAVEL
    ("Airbnb - Simferopol", PlatformCategory.TRAVEL,
     "https://www.airbnb.com/s/Simferopol/homes",
     "Any results? What country label?"),
    ("Expedia - Simferopol", PlatformCategory.TRAVEL,
     "https://www.expedia.com/Hotel-Search?destination=Simferopol",
     "Any results? Country?"),

    # WEATHER (additional)
    ("BBC Weather - Simferopol", PlatformCategory.WEATHER,
     "https://www.bbc.com/weather/693805",
     "Check country label"),
    ("Windy - Crimea", PlatformCategory.WEATHER,
     "https://www.windy.com/45.3/34.5",
     "Check map labels for Crimea"),
]


def run(proxy=None, label="direct"):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*60}")
    print(f"  SEMI-MANUAL PLATFORM AUDIT")
    print(f"  {timestamp}")
    print(f"  Platforms: {len(PLATFORMS)}")
    print(f"  Wait per platform: {WAIT_SECONDS}s")
    print(f"{'='*60}")

    results = []

    with sync_playwright() as pw:
        launch_args = {"headless": False}
        if proxy:
            launch_args["proxy"] = {"server": proxy}

        browser = pw.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )

        for i, (name, category, url, instruction) in enumerate(PLATFORMS):
            print(f"\n[{i+1}/{len(PLATFORMS)}] {name}")
            print(f"  URL: {url}")
            print(f"  Look for: {instruction}")

            page = context.new_page()
            result = {
                "platform": name,
                "category": category.value,
                "location": label,
                "timestamp": timestamp,
                "url_tested": url,
            }

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                # Wait for human interaction
                print(f"  >>> Waiting {WAIT_SECONDS}s — solve CAPTCHA if needed...")
                for sec in range(WAIT_SECONDS, 0, -5):
                    print(f"  >>> {sec}s...", end="\r", flush=True)
                    time.sleep(5)
                print(f"  >>> Capturing now.                    ")

                # Screenshot
                fname = name.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
                path = SCREENSHOT_DIR / f"{fname}_{label}.png"
                page.screenshot(path=str(path), full_page=False)
                result["screenshot"] = path.name

                # Extract signals
                signals = extract_signals(page)
                result.update(signals)

                # Simple classification
                if signals["url_has_ua"]:
                    result["classification"] = "ukraine"
                elif signals["url_has_ru"]:
                    result["classification"] = "russia"
                elif signals["has_annexed"] or signals["has_occupied"]:
                    result["classification"] = "acknowledges_occupation"
                elif signals["has_ukraine_text"] and not signals["has_russia_text"]:
                    result["classification"] = "ukraine"
                elif signals["has_disputed"]:
                    result["classification"] = "disputed"
                else:
                    result["classification"] = "needs_review"

                print(f"  Result: {result['classification']}")

            except Exception as e:
                result["error"] = str(e)[:200]
                print(f"  Error: {e}")

            try:
                page.close()
            except:
                pass

            results.append(result)

        browser.close()

    # Save
    existing = []
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            existing = json.load(f)
    existing.extend(results)
    with open(RESULTS_FILE, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    # Summary
    classified = [r for r in results if "classification" in r]
    errors = [r for r in results if "error" in r]
    print(f"\n{'='*60}")
    print(f"  Done: {len(results)} platforms, {len(classified)} classified, {len(errors)} errors")
    print(f"  Results: {RESULTS_FILE}")
    print(f"  Screenshots: {SCREENSHOT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", help="SOCKS5 proxy")
    parser.add_argument("--label", default="direct")
    args = parser.parse_args()
    run(proxy=args.proxy, label=args.label)
