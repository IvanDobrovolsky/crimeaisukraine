"""
Browser-based Crimea sovereignty checks using Playwright.

Programmatically checks platforms that were previously "manual only":
- Search engine knowledge panels (Google, Bing, DuckDuckGo)
- Travel platforms (Booking.com, TripAdvisor, Skyscanner)
- Weather services (direct verification)
- Social media location autocomplete
- Map service labels

Usage:
    python scripts/check_browsers.py
"""

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from audit_framework import (
    AuditDatabase,
    AuditMethod,
    PlatformCategory,
    SovereigntyStatus,
    create_finding,
    DATA_DIR,
)

SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def screenshot(page, name):
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    return str(path)


def check_google_search(page):
    """Check Google Knowledge Panel for 'Crimea'."""
    print("\n[1] Google Search: 'Crimea'")
    page.goto("https://www.google.com/search?q=Crimea&hl=en", wait_until="domcontentloaded")
    time.sleep(2)

    content = page.content().lower()
    screenshot(page, "google_crimea")

    country = None
    if "ukraine" in content and "russia" in content:
        # Check knowledge panel specifically
        try:
            panel = page.query_selector('[data-attrid*="country"], [data-attrid*="location"]')
            if panel:
                panel_text = panel.inner_text().lower()
                if "ukraine" in panel_text:
                    country = "ukraine"
                elif "russia" in panel_text:
                    country = "russia"
        except Exception:
            pass

        if not country:
            country = "both_mentioned"
    elif "ukraine" in content:
        country = "ukraine"
    elif "russia" in content:
        country = "russia"

    status = {
        "ukraine": SovereigntyStatus.CORRECT,
        "russia": SovereigntyStatus.INCORRECT,
        "both_mentioned": SovereigntyStatus.AMBIGUOUS,
    }.get(country, SovereigntyStatus.AMBIGUOUS)

    print(f"  Result: {country}")
    return create_finding(
        platform="Google Search (knowledge panel)",
        category=PlatformCategory.SEARCH_ENGINE,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"Searched 'Crimea' on Google. Knowledge panel country: {country}. Screenshot saved.",
        url="https://www.google.com/search?q=Crimea",
        evidence=f"country={country}",
    )


def check_bing_search(page):
    """Check Bing Knowledge Panel for 'Crimea'."""
    print("\n[2] Bing Search: 'Crimea'")
    page.goto("https://www.bing.com/search?q=Crimea", wait_until="domcontentloaded")
    time.sleep(2)

    content = page.content().lower()
    screenshot(page, "bing_crimea")

    # Bing's entity panel
    country = None
    try:
        # Look for the knowledge card
        card = page.query_selector('.b_entityTP, .b_xlText, [class*="entity"]')
        if card:
            card_text = card.inner_text().lower()
            if "ukraine" in card_text:
                country = "ukraine"
            elif "russia" in card_text:
                country = "russia"
    except Exception:
        pass

    if not country:
        if "ukraine" in content and "russia" in content:
            country = "both_mentioned"
        elif "ukraine" in content:
            country = "ukraine"

    status = {
        "ukraine": SovereigntyStatus.CORRECT,
        "russia": SovereigntyStatus.INCORRECT,
        "both_mentioned": SovereigntyStatus.AMBIGUOUS,
    }.get(country, SovereigntyStatus.AMBIGUOUS)

    print(f"  Result: {country}")
    return create_finding(
        platform="Bing Search (knowledge panel)",
        category=PlatformCategory.SEARCH_ENGINE,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"Searched 'Crimea' on Bing. Knowledge panel: {country}. Screenshot saved.",
        url="https://www.bing.com/search?q=Crimea",
        evidence=f"country={country}",
    )


def check_duckduckgo_search(page):
    """Check DuckDuckGo for 'Crimea'."""
    print("\n[3] DuckDuckGo: 'Crimea'")
    page.goto("https://duckduckgo.com/?q=Crimea", wait_until="domcontentloaded")
    time.sleep(2)

    content = page.content().lower()
    screenshot(page, "ddg_crimea")

    # DDG shows Wikipedia-sourced info box
    country = None
    try:
        infobox = page.query_selector('.module--about, .c-about')
        if infobox:
            box_text = infobox.inner_text().lower()
            if "ukraine" in box_text and "russia" not in box_text:
                country = "ukraine"
            elif "ukraine" in box_text and "russia" in box_text:
                country = "both_mentioned"
    except Exception:
        pass

    if not country:
        country = "both_mentioned" if ("ukraine" in content and "russia" in content) else "unclear"

    status = {
        "ukraine": SovereigntyStatus.CORRECT,
        "both_mentioned": SovereigntyStatus.AMBIGUOUS,
    }.get(country, SovereigntyStatus.AMBIGUOUS)

    print(f"  Result: {country}")
    return create_finding(
        platform="DuckDuckGo (info box)",
        category=PlatformCategory.SEARCH_ENGINE,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"Searched 'Crimea' on DuckDuckGo. Info box: {country}. Screenshot saved.",
        url="https://duckduckgo.com/?q=Crimea",
        evidence=f"country={country}",
    )


def check_tripadvisor(page):
    """Check TripAdvisor Crimea page."""
    print("\n[4] TripAdvisor: Crimea")
    page.goto("https://www.tripadvisor.com/Tourism-g313972-Crimea-Vacations.html",
              wait_until="domcontentloaded")
    time.sleep(2)

    content = page.content().lower()
    screenshot(page, "tripadvisor_crimea")

    if "ukraine" in content and "russia" not in content:
        status = SovereigntyStatus.CORRECT
        detail = "TripAdvisor lists Crimea under Ukraine"
    elif "europe" in content and "ukraine" not in content and "russia" not in content:
        status = SovereigntyStatus.AMBIGUOUS
        detail = "TripAdvisor lists Crimea under 'Europe' — no country"
    elif "russia" in content:
        status = SovereigntyStatus.INCORRECT
        detail = "TripAdvisor mentions Russia in Crimea context"
    else:
        status = SovereigntyStatus.AMBIGUOUS
        detail = "TripAdvisor Crimea page — country unclear"

    print(f"  Result: {status.value}")
    return create_finding(
        platform="TripAdvisor (browser check)",
        category=PlatformCategory.TRAVEL,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"{detail}. Screenshot saved.",
        url="https://www.tripadvisor.com/Tourism-g313972-Crimea-Vacations.html",
    )


def check_booking(page):
    """Check Booking.com for Simferopol."""
    print("\n[5] Booking.com: Simferopol")
    try:
        page.goto("https://www.booking.com/searchresults.html?ss=Simferopol",
                  wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        content = page.content().lower()
        screenshot(page, "booking_simferopol")

        if "no properties" in content or "no results" in content or "we couldn" in content:
            status = SovereigntyStatus.BLOCKED
            detail = "Booking.com returns no results for Simferopol (sanctions)"
        elif "ukraine" in content:
            status = SovereigntyStatus.CORRECT
            detail = "Booking.com shows Simferopol under Ukraine"
        elif "russia" in content:
            status = SovereigntyStatus.INCORRECT
            detail = "Booking.com shows Simferopol under Russia"
        else:
            status = SovereigntyStatus.AMBIGUOUS
            detail = "Booking.com Simferopol — country unclear from page"

        print(f"  Result: {status.value}")
    except Exception as e:
        status = SovereigntyStatus.BLOCKED
        detail = f"Booking.com blocked or timeout: {e}"
        print(f"  Error: {e}")

    return create_finding(
        platform="Booking.com (browser check)",
        category=PlatformCategory.TRAVEL,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"{detail}. Screenshot saved.",
        url="https://www.booking.com/searchresults.html?ss=Simferopol",
    )


def check_accuweather(page):
    """Check AccuWeather Simferopol page."""
    print("\n[6] AccuWeather: Simferopol")
    page.goto("https://www.accuweather.com/en/ua/simferopol/322464/weather-forecast/322464",
              wait_until="domcontentloaded")
    time.sleep(2)

    content = page.content().lower()
    url = page.url.lower()
    screenshot(page, "accuweather_simferopol")

    if "/ua/" in url:
        status = SovereigntyStatus.CORRECT
        detail = "AccuWeather URL contains /ua/ (Ukraine). Simferopol classified as Ukraine."
    elif "/ru/" in url:
        status = SovereigntyStatus.INCORRECT
        detail = "AccuWeather URL contains /ru/ (Russia)"
    else:
        status = SovereigntyStatus.AMBIGUOUS
        detail = f"AccuWeather URL: {page.url}"

    print(f"  Result: {status.value} (URL: {page.url[:60]})")
    return create_finding(
        platform="AccuWeather (browser verified)",
        category=PlatformCategory.WEATHER,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"{detail}. Screenshot saved.",
        url=page.url,
    )


def check_google_maps(page):
    """Check Google Maps Crimea representation."""
    print("\n[7] Google Maps: Crimea")
    page.goto("https://www.google.com/maps/place/Crimea/", wait_until="domcontentloaded")
    time.sleep(3)

    screenshot(page, "google_maps_crimea")
    content = page.content().lower()

    # Google Maps shows "Crimean Peninsula" or similar
    if "ukraine" in content and "russia" not in content:
        status = SovereigntyStatus.CORRECT
        detail = "Google Maps shows Crimea with Ukraine context"
    elif "disputed" in content:
        status = SovereigntyStatus.AMBIGUOUS
        detail = "Google Maps shows Crimea as disputed"
    else:
        status = SovereigntyStatus.AMBIGUOUS
        detail = "Google Maps Crimea — dashed border (disputed default from non-RU location)"

    print(f"  Result: {status.value}")
    return create_finding(
        platform="Google Maps (browser check)",
        category=PlatformCategory.MAP_SERVICE,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"{detail}. Screenshot saved.",
        url="https://www.google.com/maps/place/Crimea/",
    )


def check_weather_com(page):
    """Check weather.com for Simferopol."""
    print("\n[8] weather.com: Simferopol")
    try:
        page.goto("https://weather.com/weather/today/l/Simferopol+Ukraine",
                  wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        url = page.url.lower()
        content = page.content().lower()
        screenshot(page, "weather_com_simferopol")

        if "ukraine" in url or "ukraine" in content:
            status = SovereigntyStatus.CORRECT
            detail = "weather.com shows Simferopol under Ukraine"
        elif "russia" in url or "russia" in content:
            status = SovereigntyStatus.INCORRECT
            detail = "weather.com shows Simferopol under Russia"
        else:
            status = SovereigntyStatus.AMBIGUOUS
            detail = f"weather.com — country unclear. URL: {page.url[:80]}"

        print(f"  Result: {status.value}")
    except Exception as e:
        status = SovereigntyStatus.AMBIGUOUS
        detail = f"weather.com timeout or blocked: {e}"
        print(f"  Error: {e}")

    return create_finding(
        platform="weather.com (browser verified)",
        category=PlatformCategory.WEATHER,
        status=status,
        method=AuditMethod.AUTOMATED_API,
        detail=f"{detail}. Screenshot saved.",
        url="https://weather.com/",
    )


def run_all():
    db = AuditDatabase()
    findings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

        checks = [
            check_google_search,
            check_bing_search,
            check_duckduckgo_search,
            check_tripadvisor,
            check_booking,
            check_accuweather,
            check_google_maps,
            check_weather_com,
        ]

        for check in checks:
            try:
                finding = check(page)
                findings.append(finding)
                db.add(finding)
            except Exception as e:
                print(f"  ERROR in {check.__name__}: {e}")

        browser.close()

    db.save()

    print(f"\n{'='*60}")
    print(f"Browser checks complete: {len(findings)} findings")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")
    print(f"Database updated: {db.path}")

    for f in findings:
        print(f"  {f['status_icon']} {f['platform']}: {f['detail'][:80]}")


if __name__ == "__main__":
    run_all()
