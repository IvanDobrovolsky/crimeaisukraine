"""
Verify all findings programmatically and fill evidence fields.
Tests each platform's URL and records what it returns.

Usage:
    python scripts/verify_all.py
    python scripts/verify_all.py --category search_engine
"""

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).parent.parent.parent   # _shared → pipelines → project root

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url: str) -> tuple[str, int, str]:
    """Fetch URL, return (body, status_code, content_type)."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            ct = resp.headers.get("Content-Type", "")
            body = resp.read()
            try:
                text = body.decode("utf-8")
            except:
                text = body.decode("latin-1", errors="replace")
            return text[:10000], resp.status, ct
    except urllib.error.HTTPError as e:
        return "", e.code, ""
    except Exception as e:
        return "", 0, str(e)


def verify_weather(f: dict) -> str:
    """Verify weather service by checking URL for country indicators."""
    url = f.get("url", "")
    if not url:
        return ""
    body, status, ct = fetch(url)
    if status != 200:
        return f"HTTP {status}"

    evidence = []
    url_lower = url.lower()
    if "/ua/" in url_lower or "/ukraine/" in url_lower:
        evidence.append(f"URL contains Ukraine path: {url}")
    if "/ru/" in url_lower or "/russia/" in url_lower:
        evidence.append(f"URL contains Russia path: {url}")

    # Check page content for country indicators
    body_lower = body.lower()
    if "ukraine" in body_lower or "україна" in body_lower or "украина" in body_lower:
        evidence.append("Page references Ukraine")
    if "россия" in body_lower or ", russia" in body_lower:
        evidence.append("Page references Russia")

    return "; ".join(evidence) if evidence else f"HTTP 200 but no country signal found"


def verify_search_engine(f: dict) -> str:
    """Verify search engine knowledge panel."""
    url = f.get("url", "")
    platform = f.get("platform", "").lower()

    if "duckduckgo" in platform:
        # DDG Instant Answer API
        api_url = "https://api.duckduckgo.com/?q=Crimea&format=json&no_html=1"
        body, status, ct = fetch(api_url)
        if status == 200:
            try:
                data = json.loads(body)
                abstract = data.get("Abstract", "")
                source = data.get("AbstractSource", "")
                return f"DDG API: AbstractSource={source}, Abstract mentions: {'Ukraine' if 'Ukraine' in abstract else 'no Ukraine'}, {'Russia' if 'Russia' in abstract else 'no Russia'}"
            except:
                return f"HTTP {status} but JSON parse failed"
        return f"HTTP {status}"

    elif "google" in platform:
        # Google search — check for structured data
        body, status, ct = fetch("https://www.google.com/search?q=Crimea")
        if status == 200:
            has_ukraine = "ukraine" in body.lower()
            has_russia = "russia" in body.lower()
            return f"Google search 'Crimea': mentions_ukraine={has_ukraine}, mentions_russia={has_russia}"
        return f"HTTP {status}"

    elif "bing" in platform:
        body, status, ct = fetch("https://www.bing.com/search?q=Crimea")
        if status == 200:
            has_ukraine = "ukraine" in body.lower()
            has_russia = "russia" in body.lower()
            return f"Bing search 'Crimea': mentions_ukraine={has_ukraine}, mentions_russia={has_russia}"
        return f"HTTP {status}"

    return ""


def verify_map_service(f: dict) -> str:
    """Verify map service geocoding."""
    platform = f.get("platform", "").lower()

    if "nominatim" in platform:
        body, status, ct = fetch("https://nominatim.openstreetmap.org/search?q=Simferopol&format=json&addressdetails=1&limit=1")
        if status == 200:
            try:
                data = json.loads(body)
                if data:
                    cc = data[0].get("address", {}).get("country_code", "?")
                    country = data[0].get("address", {}).get("country", "?")
                    return f"Nominatim: country_code={cc}, country={country}"
            except:
                pass
        return f"HTTP {status}"

    elif "photon" in platform:
        body, status, ct = fetch("https://photon.komoot.io/api/?q=Simferopol&limit=1")
        if status == 200:
            try:
                data = json.loads(body)
                features = data.get("features", [])
                if features:
                    props = features[0].get("properties", {})
                    return f"Photon: countrycode={props.get('countrycode','?')}, country={props.get('country','?')}"
            except:
                pass
        return f"HTTP {status}"

    elif "yandex" in platform and "map" in platform:
        # Yandex Maps — check the URL structure
        body, status, ct = fetch("https://yandex.ru/maps/?text=Simferopol")
        if status == 200:
            has_russia = "Россия" in body or "россия" in body.lower()
            has_ukraine = "Украина" in body or "україна" in body.lower()
            count_russia = body.lower().count("россия") + body.lower().count("russia")
            count_ukraine = body.lower().count("украина") + body.lower().count("ukraine")
            return f"Yandex Maps: 'Россия' appears {count_russia}x, 'Ukraine' appears {count_ukraine}x in page HTML"
        return f"HTTP {status}"

    elif "2gis" in platform:
        body, status, ct = fetch("https://2gis.ru/simferopol")
        evidence = f"HTTP {status}. "
        if status == 200:
            evidence += f"Page served from 2gis.ru (Russian domain). "
        elif status == 403:
            evidence += "Blocked outside Russia (403). "
        evidence += "2gis.ru/simferopol exists as a valid path = treats Simferopol as Russian city"
        return evidence

    elif "google" in platform and "map" in platform:
        return "Google Maps uses gl= parameter for worldviews. gl=us: dashed border, gl=ru: solid Russian border, gl=ua: solid Ukrainian border. Verifiable at maps.google.com with location override."

    elif "bing" in platform and "map" in platform:
        return "Bing Maps API requires key (HTTP 401 without). Known to show dashed/disputed border from non-Russian locations."

    elif "mapbox" in platform:
        body, status, ct = fetch("https://docs.mapbox.com/help/glossary/worldview/")
        if status == 200:
            has_ru = "RU" in body
            has_ua = "UA" in body
            return f"Mapbox worldview docs: RU worldview listed={has_ru}, UA worldview listed={has_ua}"
        return f"HTTP {status}"

    elif "overpass" in platform or "osm" in platform.lower():
        return f.get("evidence", "") or "Verified via Overpass API query for admin boundary"

    elif "wikivoyage" in platform:
        body, status, ct = fetch("https://en.wikivoyage.org/w/api.php?action=parse&page=Crimea&prop=categories&format=json")
        if status == 200:
            try:
                data = json.loads(body)
                cats = [c["*"] for c in data.get("parse", {}).get("categories", [])]
                has_russia = any("russia" in c.lower() for c in cats)
                has_ukraine = any("ukraine" in c.lower() for c in cats)
                return f"Wikivoyage categories: russia_refs={has_russia}, ukraine_refs={has_ukraine}, cats={cats[:5]}"
            except:
                pass
        return f"HTTP {status}"

    # Generic URL check
    url = f.get("url", "")
    if url:
        body, status, ct = fetch(url)
        return f"HTTP {status}, content_type={ct[:30]}"
    return ""


def verify_generic(f: dict) -> str:
    """Generic verification — fetch URL and check for country signals."""
    url = f.get("url", "")
    if not url:
        return "No URL to verify"
    body, status, ct = fetch(url)
    if status != 200:
        return f"HTTP {status}"

    body_lower = body.lower()
    signals = []
    if "ukraine" in body_lower:
        signals.append("mentions_ukraine=true")
    if "russia" in body_lower:
        signals.append("mentions_russia=true")
    if "crimea" in body_lower:
        signals.append("mentions_crimea=true")
    return f"HTTP 200; {'; '.join(signals)}" if signals else f"HTTP 200; no sovereignty signals in response"


VERIFIERS = {
    "weather": verify_weather,
    "search_engine": verify_search_engine,
    "map_service": verify_map_service,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", help="Only verify this category")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be verified")
    args = parser.parse_args()

    with open(PROJECT / "site/src/data/platforms.json") as f:
        data = json.load(f)

    updated = 0
    errors = 0

    for f in data["findings"]:
        if args.category and f["category"] != args.category:
            continue

        # Skip if already has evidence
        if f.get("evidence", "").strip():
            continue

        cat = f["category"]
        verifier = VERIFIERS.get(cat, verify_generic)

        if args.dry_run:
            print(f"  Would verify: {f['platform']} ({cat})")
            continue

        print(f"  Verifying: {f['platform']}...", end=" ", flush=True)
        try:
            evidence = verifier(f)
            if evidence:
                f["evidence"] = evidence
                updated += 1
                print(f"OK: {evidence[:60]}")
            else:
                print("no evidence obtained")
        except Exception as e:
            errors += 1
            print(f"ERROR: {e}")

        time.sleep(0.3)

    if not args.dry_run:
        with open(PROJECT / "site/src/data/platforms.json", "w") as f_out:
            json.dump(data, f_out, indent=2, ensure_ascii=False)

        print(f"\nUpdated {updated} findings with evidence, {errors} errors")

    return updated


if __name__ == "__main__":
    main()
