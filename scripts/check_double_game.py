"""
Double-game detection: find platforms that show different Crimea
classifications depending on the viewer's geographic location.

Methodology:
  1. Test each platform from multiple VPN exit nodes
  2. Compare results across locations
  3. Flag platforms where the classification CHANGES

This is the novel methodological contribution — systematic detection
of geo-fenced sovereignty representation.

For CAPTCHA-protected sites: the script pauses for manual solving.

Usage:
    # Direct (no VPN):
    python scripts/check_double_game.py --label US

    # With VPN proxy:
    python scripts/check_double_game.py --proxy socks5://127.0.0.1:1080 --label DE

    # Semi-manual mode (30s pause for CAPTCHA solving):
    python scripts/check_double_game.py --label US --wait 30

    # After running from multiple locations, analyze:
    python scripts/check_double_game.py --analyze
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

from audit_framework import DATA_DIR

SCREENSHOT_DIR = DATA_DIR / "screenshots" / "double_game"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_FILE = DATA_DIR / "double_game_results.json"


def dismiss_cookies(page):
    selectors = [
        'button:has-text("Accept")', 'button:has-text("Accept all")',
        'button:has-text("Agree")', 'button:has-text("OK")',
        'button:has-text("Got it")', 'button:has-text("I agree")',
        '[id*="cookie"] button', '[class*="consent"] button',
    ]
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                time.sleep(1)
                return
        except:
            continue


def wait_for_human(page, seconds, platform):
    """Pause for human to solve CAPTCHA or interact."""
    print(f"\n  >>> WAITING {seconds}s for manual interaction on {platform}")
    print(f"  >>> Solve any CAPTCHA, dismiss popups, then wait...")
    for i in range(seconds, 0, -5):
        print(f"  >>> {i}s remaining...", end="\r")
        time.sleep(5)
    print(f"  >>> Capturing result now.")


def extract_crimea_signals(page):
    """Extract sovereignty signals from page content."""
    content = page.content().lower()
    url = page.url.lower()

    signals = {
        "url": page.url,
        "has_ukraine": any(w in content for w in ["ukraine", "україна", "украина"]),
        "has_russia": any(w in content for w in [
            "russia", "россия", "російська", "russian federation"
        ]),
        "has_disputed": any(w in content for w in ["disputed", "contested", "спірний"]),
        "has_annexed": any(w in content for w in ["annexed", "annexation", "анексія", "аннексия"]),
        "has_occupied": any(w in content for w in ["occupied", "occupation", "окупований"]),
        "url_ua": "/ua/" in url or "/ukraine/" in url,
        "url_ru": "/ru/" in url or "/russia/" in url,
    }
    return signals


def check_platform(context, platform_name, url, label, wait_seconds=0):
    """Check a single platform and return signals."""
    print(f"\n[{platform_name}] from {label}")
    page = context.new_page()
    result = {
        "platform": platform_name,
        "location": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        dismiss_cookies(page)
        time.sleep(1)

        if wait_seconds > 0:
            wait_for_human(page, wait_seconds, platform_name)

        # Screenshot
        path = SCREENSHOT_DIR / f"{platform_name.lower().replace(' ','_').replace('.','_')}_{label}.png"
        page.screenshot(path=str(path), full_page=False)
        result["screenshot"] = path.name

        # Extract signals
        signals = extract_crimea_signals(page)
        result.update(signals)

        # Classify
        if signals["url_ua"] or (signals["has_ukraine"] and not signals["has_russia"]):
            result["classification"] = "ukraine"
        elif signals["url_ru"] or (signals["has_russia"] and not signals["has_ukraine"]):
            result["classification"] = "russia"
        elif signals["has_disputed"]:
            result["classification"] = "disputed"
        elif signals["has_ukraine"] and signals["has_russia"]:
            result["classification"] = "both_mentioned"
        else:
            result["classification"] = "unclear"

        print(f"  Classification: {result['classification']}")
        print(f"  UA:{signals['has_ukraine']} RU:{signals['has_russia']} "
              f"disputed:{signals['has_disputed']} annexed:{signals['has_annexed']}")

    except Exception as e:
        result["error"] = str(e)[:200]
        print(f"  Error: {e}")

    try:
        page.close()
    except:
        pass

    return result


# Platforms to test — URLs that reference Crimea
PLATFORMS = [
    # Search engines
    ("Google Search", "https://www.google.com/search?q=Crimea&hl=en"),
    ("Bing Search", "https://www.bing.com/search?q=Crimea"),
    ("DuckDuckGo", "https://duckduckgo.com/?q=Crimea"),
    ("Yahoo Search", "https://search.yahoo.com/search?p=Crimea"),
    ("Yandex Search", "https://yandex.com/search/?text=Crimea"),
    ("Brave Search", "https://search.brave.com/search?q=Crimea"),
    ("Ecosia", "https://www.ecosia.org/search?q=Crimea"),

    # Maps
    ("Google Maps", "https://www.google.com/maps/@45.3,34.5,8z"),
    ("Bing Maps", "https://www.bing.com/maps?cp=45.3~34.5&lvl=8"),

    # Weather (should be consistent regardless of location)
    ("AccuWeather", "https://www.accuweather.com/en/search-locations?query=simferopol"),

    # Travel
    ("Booking.com", "https://www.booking.com/searchresults.html?ss=Simferopol"),
    ("TripAdvisor", "https://www.tripadvisor.com/Tourism-g313972-Crimea-Vacations.html"),

    # Reference
    ("Wikipedia EN", "https://en.wikipedia.org/wiki/Crimea"),

    # Media
    ("BBC", "https://www.bbc.com/news/topics/c1ez1k0ezklt"),
    ("Al Jazeera", "https://www.aljazeera.com/where/crimea/"),
]


def run_check(proxy=None, label="direct", wait_seconds=0):
    """Run all platform checks from one location."""
    print(f"{'='*60}")
    print(f"  DOUBLE-GAME DETECTION")
    print(f"  Location: {label}")
    print(f"  Proxy: {proxy or 'none'}")
    print(f"  Wait for CAPTCHA: {wait_seconds}s")
    print(f"{'='*60}")

    results = []

    with sync_playwright() as pw:
        launch_args = {"headless": False}
        if proxy:
            launch_args["proxy"] = {"server": proxy}

        browser = pw.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )

        # Detect actual location
        det_page = context.new_page()
        try:
            det_page.goto("http://ip-api.com/json/?fields=country,countryCode,city,query",
                         timeout=10000)
            loc_data = json.loads(det_page.inner_text("pre"))
            print(f"\n  Detected: {loc_data.get('country')} ({loc_data.get('countryCode')}), "
                  f"{loc_data.get('city')}, IP: {loc_data.get('query')}")
        except:
            print(f"\n  Could not detect location")
        det_page.close()

        for platform_name, url in PLATFORMS:
            result = check_platform(context, platform_name, url, label, wait_seconds)
            results.append(result)
            time.sleep(2)

        browser.close()

    # Save (append)
    existing = []
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            existing = json.load(f)
    existing.extend(results)
    with open(RESULTS_FILE, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  Done: {len(results)} platforms from {label}")
    print(f"  Saved to: {RESULTS_FILE}")
    print(f"{'='*60}")


def analyze():
    """Analyze results across locations to detect double-game platforms."""
    if not RESULTS_FILE.exists():
        print("No results file. Run checks from multiple locations first.")
        return

    with open(RESULTS_FILE) as f:
        data = json.load(f)

    # Group by platform
    by_platform = {}
    for r in data:
        name = r.get("platform", "?")
        if name not in by_platform:
            by_platform[name] = []
        by_platform[name].append(r)

    print(f"\n{'='*60}")
    print(f"  DOUBLE-GAME ANALYSIS")
    print(f"  Platforms: {len(by_platform)}")
    print(f"  Total checks: {len(data)}")
    print(f"{'='*60}")

    double_game = []
    consistent = []
    insufficient = []

    for name, checks in sorted(by_platform.items()):
        locations = set(c.get("location") for c in checks)
        classifications = set(c.get("classification") for c in checks if "classification" in c)
        errors = [c for c in checks if "error" in c]

        if len(locations) < 2:
            insufficient.append(name)
            continue

        if len(classifications) > 1 and "unclear" not in classifications:
            # Different classifications from different locations = double game!
            double_game.append({
                "platform": name,
                "locations": {c.get("location"): c.get("classification") for c in checks if "classification" in c},
            })
        elif len(classifications) == 1:
            consistent.append({
                "platform": name,
                "classification": classifications.pop(),
                "locations_tested": len(locations),
            })

    print(f"\n  DOUBLE-GAME DETECTED ({len(double_game)}):")
    for dg in double_game:
        print(f"    {dg['platform']}:")
        for loc, cls in dg["locations"].items():
            icon = {"ukraine": "UA", "russia": "RU", "disputed": "??", "both_mentioned": "both"}.get(cls, cls)
            print(f"      from {loc}: {icon}")

    print(f"\n  CONSISTENT ({len(consistent)}):")
    for c in consistent:
        print(f"    {c['platform']}: {c['classification']} (tested from {c['locations_tested']} locations)")

    print(f"\n  INSUFFICIENT DATA ({len(insufficient)}):")
    for name in insufficient:
        print(f"    {name}: only tested from 1 location")

    # Save analysis
    analysis = {
        "double_game": double_game,
        "consistent": consistent,
        "insufficient": insufficient,
        "total_platforms": len(by_platform),
        "total_checks": len(data),
    }
    analysis_path = DATA_DIR / "double_game_analysis.json"
    with open(analysis_path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"\n  Analysis saved to: {analysis_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", help="SOCKS5 proxy (e.g., socks5://127.0.0.1:1080)")
    parser.add_argument("--label", default="direct", help="Location label (US, DE, UA, RU)")
    parser.add_argument("--wait", type=int, default=0, help="Seconds to wait for CAPTCHA solving")
    parser.add_argument("--analyze", action="store_true", help="Analyze collected results for double-game")
    args = parser.parse_args()

    if args.analyze:
        analyze()
    else:
        run_check(proxy=args.proxy, label=args.label, wait_seconds=args.wait)
