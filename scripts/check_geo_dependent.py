"""
Multi-location browser testing for geo-dependent platforms.

Tests how platforms show Crimea from different geographic perspectives
by connecting through different proxy/VPN exit nodes.

Requires: ProtonVPN or SOCKS proxy configured.
Usage:
    # Test from current location (no proxy):
    python scripts/check_geo_dependent.py

    # Test through SOCKS proxy (e.g., ProtonVPN):
    python scripts/check_geo_dependent.py --proxy socks5://127.0.0.1:1080

    # Test specific country exit:
    python scripts/check_geo_dependent.py --proxy socks5://127.0.0.1:1080 --label "DE"
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

SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_FILE = DATA_DIR / "geo_dependent_results.json"


def dismiss_cookies(page):
    """Try to dismiss common cookie consent banners."""
    selectors = [
        'button:has-text("Accept")', 'button:has-text("Accept all")',
        'button:has-text("Agree")', 'button:has-text("OK")',
        'button:has-text("Got it")', 'button:has-text("I agree")',
        'button:has-text("Akzeptieren")', 'button:has-text("Принять")',
        '[id*="cookie"] button', '[class*="cookie"] button',
        '[id*="consent"] button', '[class*="consent"] button',
        'button[data-testid*="accept"]',
    ]
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                time.sleep(1)
                return True
        except:
            continue
    return False


def detect_country(page, label=""):
    """Detect what country the current connection appears to be from."""
    try:
        page.goto("http://ip-api.com/json/?fields=country,countryCode,city,query",
                  wait_until="domcontentloaded", timeout=10000)
        data = json.loads(page.inner_text("pre"))
        cc = data.get("countryCode", "??")
        city = data.get("city", "")
        ip = data.get("query", "")
        print(f"  Location: {data.get('country')} ({cc}), {city}, IP: {ip}")
        return cc
    except Exception as e:
        print(f"  Could not detect location: {e}")
        return label or "??"


def check_google_maps_crimea(page, location_label):
    """Check Google Maps Crimea border rendering."""
    print(f"\n[Google Maps] from {location_label}")
    try:
        page.goto("https://www.google.com/maps/@45.3,34.5,8z", wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
        dismiss_cookies(page)
        time.sleep(2)
        path = SCREENSHOT_DIR / f"google_maps_{location_label}.png"
        page.screenshot(path=str(path), full_page=False)
        print(f"  Screenshot: {path.name}")

        # Check for Crimea-related text
        content = page.content().lower()
        has_ukraine = "ukraine" in content or "україна" in content
        has_russia = "russia" in content or "россия" in content
        has_crimea = "crimea" in content or "крим" in content or "крым" in content

        return {
            "platform": "Google Maps",
            "location": location_label,
            "has_ukraine": has_ukraine,
            "has_russia": has_russia,
            "has_crimea": has_crimea,
            "screenshot": path.name,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {"platform": "Google Maps", "location": location_label, "error": str(e)}


def check_google_search_crimea(page, location_label):
    """Check Google Search knowledge panel for Crimea."""
    print(f"\n[Google Search] from {location_label}")
    try:
        page.goto(f"https://www.google.com/search?q=Crimea&hl=en", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        dismiss_cookies(page)
        path = SCREENSHOT_DIR / f"google_search_{location_label}.png"
        page.screenshot(path=str(path), full_page=False)
        print(f"  Screenshot: {path.name}")

        content = page.content().lower()
        # Look for country in knowledge panel
        country = "unclear"
        if "peninsula" in content and "ukraine" in content:
            country = "mentions_ukraine"
        if "russia" in content:
            country = "mentions_both" if country == "mentions_ukraine" else "mentions_russia"

        return {
            "platform": "Google Search",
            "location": location_label,
            "country_detected": country,
            "screenshot": path.name,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {"platform": "Google Search", "location": location_label, "error": str(e)}


def check_bing_maps(page, location_label):
    """Check Bing Maps Crimea rendering."""
    print(f"\n[Bing Maps] from {location_label}")
    try:
        page.goto("https://www.bing.com/maps?cp=45.3~34.5&lvl=8", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        path = SCREENSHOT_DIR / f"bing_maps_{location_label}.png"
        page.screenshot(path=str(path), full_page=False)
        print(f"  Screenshot: {path.name}")

        content = page.content().lower()
        return {
            "platform": "Bing Maps",
            "location": location_label,
            "has_ukraine": "ukraine" in content,
            "has_russia": "russia" in content,
            "screenshot": path.name,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {"platform": "Bing Maps", "location": location_label, "error": str(e)}


def check_accuweather(page, location_label):
    """Check AccuWeather Simferopol classification."""
    print(f"\n[AccuWeather] from {location_label}")
    try:
        page.goto("https://www.accuweather.com/en/search-locations?query=simferopol",
                  wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        path = SCREENSHOT_DIR / f"accuweather_{location_label}.png"
        page.screenshot(path=str(path), full_page=False)

        content = page.content().lower()
        url = page.url.lower()
        country = "ukraine" if "/ua/" in url or "ukraine" in content else "russia" if "/ru/" in url else "unclear"
        print(f"  Country: {country} (URL: {page.url[:60]})")

        return {
            "platform": "AccuWeather",
            "location": location_label,
            "country_detected": country,
            "url": page.url,
            "screenshot": path.name,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {"platform": "AccuWeather", "location": location_label, "error": str(e)}


def check_booking(page, location_label):
    """Check Booking.com for Simferopol."""
    print(f"\n[Booking.com] from {location_label}")
    try:
        page.goto("https://www.booking.com/searchresults.html?ss=Simferopol",
                  wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        dismiss_cookies(page)
        time.sleep(2)
        path = SCREENSHOT_DIR / f"booking_{location_label}.png"
        page.screenshot(path=str(path), full_page=False)

        content = page.content().lower()
        if "no properties" in content or "no results" in content or "we couldn" in content:
            status = "blocked"
        elif "ukraine" in content:
            status = "ukraine"
        elif "russia" in content:
            status = "russia"
        else:
            status = "unclear"
        print(f"  Status: {status}")

        return {
            "platform": "Booking.com",
            "location": location_label,
            "status": status,
            "screenshot": path.name,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {"platform": "Booking.com", "location": location_label, "error": str(e)}


def check_tripadvisor(page, location_label):
    """Check TripAdvisor Crimea page."""
    print(f"\n[TripAdvisor] from {location_label}")
    try:
        page.goto("https://www.tripadvisor.com/Tourism-g313972-Crimea-Vacations.html",
                  wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        dismiss_cookies(page)
        path = SCREENSHOT_DIR / f"tripadvisor_{location_label}.png"
        page.screenshot(path=str(path), full_page=False)

        content = page.content().lower()
        breadcrumb = ""
        try:
            bc = page.query_selector('[data-automation="breadcrumb"], .breadcrumb, nav[aria-label]')
            if bc:
                breadcrumb = bc.inner_text().lower()
        except:
            pass

        country = "unclear"
        if "ukraine" in breadcrumb:
            country = "ukraine"
        elif "russia" in breadcrumb:
            country = "russia"
        elif "europe" in breadcrumb and "ukraine" not in breadcrumb:
            country = "europe_only"
        print(f"  Breadcrumb country: {country}")

        return {
            "platform": "TripAdvisor",
            "location": location_label,
            "country_detected": country,
            "breadcrumb": breadcrumb[:100],
            "screenshot": path.name,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {"platform": "TripAdvisor", "location": location_label, "error": str(e)}


def check_wikipedia(page, location_label):
    """Check English Wikipedia Crimea intro from this location."""
    print(f"\n[Wikipedia] from {location_label}")
    try:
        page.goto("https://en.wikipedia.org/wiki/Crimea", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)
        path = SCREENSHOT_DIR / f"wikipedia_{location_label}.png"
        page.screenshot(path=str(path), full_page=False)

        # Get first paragraph
        intro = ""
        try:
            first_p = page.query_selector("#mw-content-text .mw-parser-output > p:not(.mw-empty-elt)")
            if first_p:
                intro = first_p.inner_text()[:500]
        except:
            pass
        print(f"  Intro: {intro[:100]}...")

        return {
            "platform": "Wikipedia (EN)",
            "location": location_label,
            "intro_excerpt": intro[:300],
            "screenshot": path.name,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {"platform": "Wikipedia", "location": location_label, "error": str(e)}


ALL_CHECKS = [
    check_google_search_crimea,
    check_bing_maps,
    check_accuweather,
    check_booking,
    check_tripadvisor,
    check_wikipedia,
    check_google_maps_crimea,
]


def run_all(proxy=None, label=None):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*60}")
    print(f"  GEO-DEPENDENT PLATFORM AUDIT")
    print(f"  {timestamp}")
    print(f"  Proxy: {proxy or 'none (direct connection)'}")
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
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Detect location
        location_label = detect_country(page, label or "direct")
        if label:
            location_label = label

        for check_fn in ALL_CHECKS:
            try:
                # Fresh page per check — so one failure doesn't kill the rest
                check_page = context.new_page()
                result = check_fn(check_page, location_label)
                result["timestamp"] = timestamp
                results.append(result)
                check_page.close()
            except Exception as e:
                print(f"  FAILED: {check_fn.__name__}: {e}")
                results.append({
                    "platform": check_fn.__name__,
                    "location": location_label,
                    "error": str(e),
                    "timestamp": timestamp,
                })
                try:
                    check_page.close()
                except:
                    pass
            time.sleep(3)

        browser.close()

    # Save results (append to existing)
    existing = []
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            existing = json.load(f)

    existing.extend(results)
    with open(RESULTS_FILE, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  Done. {len(results)} checks from {location_label}")
    print(f"  Results appended to: {RESULTS_FILE}")
    print(f"  Screenshots in: {SCREENSHOT_DIR}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-location Crimea sovereignty audit")
    parser.add_argument("--proxy", help="SOCKS5 proxy URL (e.g., socks5://127.0.0.1:1080)")
    parser.add_argument("--label", help="Location label (e.g., DE, US, UA, RU)")
    args = parser.parse_args()

    run_all(proxy=args.proxy, label=args.label)
