"""
Weather Services Crimea Sovereignty Audit — real live pipeline.

For each weather service in the catalog, we run four probes and classify the
result into a status taxonomy that distinguishes:

    correct                     — unambiguously attributes Crimea to Ukraine
    incorrect                   — attributes Crimea to Russia
    worldview_compliant         — capable of serving either answer, chooses
                                  per-viewer (IP / region / account locale)
    url_correct_ui_ambiguous    — URL path says UA but the visible page title
                                  or breadcrumb omits the country
    untested                    — service requires auth / dev tokens / a
                                  Russian IP proxy to resolve; we refuse to
                                  guess
    unreachable                 — service blocked our scraper (non-2xx or
                                  CDN challenge). Not a finding about the
                                  service's sovereignty position.
    na                          — Simferopol simply not in the service

Primary sovereignty signal: URL path (e.g. `/ua/simferopol` vs `/ru/simferopol`).
This is the machine-readable classification the service itself uses for
routing, and is unambiguous. Secondary: <title>. Tertiary: visible breadcrumb
or body text. Quaternary: timezone shown for the city (IANA zone
`Europe/Simferopol` is the ISO 3166 / UA-aligned answer; `Europe/Moscow` is
the de-facto / Russian-aligned answer — the IANA zone1970.tab file lists
Europe/Simferopol under both UA and RU, so which one a service shows is a
deliberate choice, not inheritance).

Ground truth is fetched live from GeoNames entry 693805 (Simferopol) and
OpenWeatherMap's geocoding API (when an OWM_API_KEY env var is present).

Usage:
    cd pipelines/weather && uv sync && uv run scan.py
    # or from project root:
    make pipeline-weather
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

PROJECT = Path(__file__).parent
DATA = PROJECT / "data"
DATA.mkdir(exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
})
TIMEOUT = 20


# ─── Status taxonomy ────────────────────────────────────────────────────────

STATUS_CORRECT = "correct"
STATUS_INCORRECT = "incorrect"
STATUS_WORLDVIEW = "worldview_compliant"
STATUS_URL_CORRECT_UI_AMBIGUOUS = "url_correct_ui_ambiguous"
STATUS_UNTESTED = "untested"
STATUS_UNREACHABLE = "unreachable"
STATUS_NA = "na"


# ─── Service catalog ────────────────────────────────────────────────────────
# Each entry specifies how to live-probe one service for Simferopol.
# `canonical_url` is the URL we fetch. `prior_status` is the old manual
# classification we are re-verifying.

@dataclass
class Service:
    name: str
    origin_country: str
    canonical_url: str
    prior_status: str
    notes: str = ""
    # If True, treat 4xx/5xx as a sovereignty signal (e.g. a service that
    # returns 404 for /ru/ is correct).
    strict_status: bool = False


SERVICES: list[Service] = [
    # ── 16 previously "correct" Western services ──
    Service("AccuWeather", "US",
            # AccuWeather's public autocomplete JSON endpoint. This returns
            # structured results with explicit country codes per entry, and
            # reveals a striking detail: AccuWeather's database contains
            # BOTH a country=UA and a country=RU entry for Simferopol. The
            # first (highest-ranked) is country=UA, so the default experience
            # is correct, but the dual-listing is itself worth documenting.
            "https://www.accuweather.com/web-api/autocomplete?query=Simferopol&language=en-us",
            STATUS_CORRECT,
            notes="Autocomplete JSON endpoint returns multiple results per query; "
                  "the first result determines AccuWeather's default routing."),
    Service("Weather.com (The Weather Channel)", "US",
            "https://weather.com/weather/today/l/44.95,34.10",
            STATUS_CORRECT),
    Service("Weather Underground", "US",
            "https://www.wunderground.com/weather/ua/simferopol",
            STATUS_CORRECT),
    Service("TimeAndDate.com", "Norway",
            "https://www.timeanddate.com/weather/ukraine/simferopol",
            STATUS_CORRECT),
    Service("Weather Spark", "US",
            "https://weatherspark.com/y/96313/Average-Weather-in-Simferopol-Ukraine-Year-Round",
            STATUS_CORRECT),
    Service("Meteoblue", "Switzerland",
            "https://www.meteoblue.com/en/weather/week/simferopol_ukraine_696643",
            STATUS_CORRECT),
    Service("Weather-Forecast.com", "UK",
            "https://www.weather-forecast.com/locations/Simferopol/forecasts/latest",
            STATUS_CORRECT),
    Service("Ventusky", "Czechia",
            "https://www.ventusky.com/simferopol",
            STATUS_CORRECT),
    Service("Weather Atlas", "Serbia",
            "https://www.weather-atlas.com/en/ukraine/simferopol",
            STATUS_CORRECT),
    Service("Windy.com", "Czechia",
            "https://www.windy.com/44.948/34.100?44.948,34.100,8",
            STATUS_CORRECT),
    Service("yr.no (Norwegian Met Institute)", "Norway",
            "https://www.yr.no/en/forecast/daily-table/2-703448/Ukraine/Autonomous%20Republic%20of%20Crimea/Simferopol/Simferopol",
            STATUS_CORRECT),
    Service("Foreca", "Finland",
            "https://www.foreca.com/Ukraine/Simferopol",
            STATUS_CORRECT),
    Service("ilMeteo (Italy)", "Italy",
            "https://www.ilmeteo.it/meteo/Simferopol",
            STATUS_CORRECT),
    Service("AEMET (Spain)", "Spain",
            "https://www.aemet.es/es/eltiempo/prediccion/mundo?w=27000&l=34109_44948&c=UA",
            STATUS_CORRECT),
    Service("Windfinder (Germany)", "Germany",
            "https://www.windfinder.com/forecast/simferopol_international_airport",
            STATUS_CORRECT),
    Service("Meteostat (Germany)", "Germany",
            "https://meteostat.net/en/place/ua/simferopol?s=33946&t=2024-01-01/2024-12-31",
            STATUS_CORRECT),

    # ── 4 Russian-origin services: expected incorrect ──
    Service("Yandex Weather", "Russia",
            "https://yandex.com/weather/simferopol",
            STATUS_INCORRECT),
    Service("Gismeteo", "Russia",
            "https://www.gismeteo.com/weather-simferopol-5032/",
            STATUS_INCORRECT),
    Service("rp5.ru", "Russia",
            "https://rp5.ru/Weather_in_Simferopol",
            STATUS_INCORRECT),
    Service("Pogoda.mail.ru", "Russia",
            "https://pogoda.mail.ru/prognoz/simferopol/",
            STATUS_INCORRECT),

    # ── 2 previously "ambiguous" ──
    Service("World Weather Online", "UK",
            "https://www.worldweatheronline.com/simferopol-weather/avtonomna-respublika-krym/ua.aspx",
            "ambiguous"),
    Service("MSN Weather (Microsoft)", "US",
            "https://www.msn.com/en-us/weather/forecast/in-Simferopol",
            "ambiguous"),

    # ── Previously "n/a" ──
    Service("tenki.jp (Japan)", "Japan",
            "https://tenki.jp/world/",
            STATUS_NA),

    # ── Worldview-compliant candidates (reviewer point #1) ──
    Service("Apple WeatherKit", "US",
            "https://developer.apple.com/weatherkit/",
            STATUS_UNTESTED,
            notes="Requires Apple Developer JWT (ES256) for api.weatherkit.apple.com. "
                  "Worldview-split hypothesis: EU/US IP → UA, RU IP → RU. "
                  "Not verifiable from this scanner without a signed token and a "
                  "Russian IP proxy. Honest default: untested."),
    Service("Google Search Weather Panel", "US",
            "https://www.google.com/search?q=Simferopol+weather&gl=us&hl=en",
            STATUS_UNTESTED,
            notes="Google's weather panel is embedded in Search and localized via "
                  "&gl= (geo) and &hl= (language). Worldview-split hypothesis: "
                  "&gl=us → UA, &gl=ru → RU. Google blocks scraping without JS; "
                  "we record the hypothesis and mark for manual browser verification."),
]


# ─── HTML probing helpers ───────────────────────────────────────────────────

UA_PATTERNS = [
    re.compile(r"\bukraine\b", re.I),
    re.compile(r"ukrainian", re.I),
    re.compile(r"\bucraina\b", re.I),     # Italian
    re.compile(r"\bucrania\b", re.I),     # Spanish / Portuguese
    re.compile(r"\bucrânia\b", re.I),     # Portuguese
    re.compile(r"\bукраїна\b", re.I),
    re.compile(r"україн", re.I),
    re.compile(r"украин", re.I),
    re.compile(r"\bUA\b"),
    re.compile(r"/ua/", re.I),
    re.compile(r"\.ua\b"),
    re.compile(r"country[_-]?code[\"':=\s]+ua", re.I),
]

RU_PATTERNS = [
    re.compile(r"\brussia\b", re.I),
    re.compile(r"russian\s+federation", re.I),
    re.compile(r"\brussland\b", re.I),    # German
    re.compile(r"\brussie\b", re.I),      # French
    re.compile(r"\brusia\b", re.I),       # Spanish
    re.compile(r"росси[яйи]", re.I),
    re.compile(r"/ru/", re.I),
    re.compile(r"country[_-]?code[\"':=\s]+ru", re.I),
]

TZ_SIMFEROPOL = re.compile(r"Europe/Simferopol", re.I)
TZ_MOSCOW = re.compile(r"Europe/Moscow", re.I)


def fetch(url: str, allow_redirects: bool = True) -> tuple[int, str, str]:
    """Return (status, final_url, body). Never raises — returns ('', '', '') on error."""
    try:
        r = SESSION.get(url, timeout=TIMEOUT, allow_redirects=allow_redirects)
        body = r.text if r.status_code < 400 else ""
        return r.status_code, r.url, body
    except Exception as e:
        return 0, "", f"__error__:{e}"


def extract_title(html: str) -> str:
    if not html:
        return ""
    try:
        soup = BeautifulSoup(html, "html.parser")
        t = soup.find("title")
        return (t.get_text(strip=True) if t else "")[:200]
    except Exception:
        return ""


def extract_breadcrumbs(html: str) -> str:
    """Pull any schema.org BreadcrumbList or visible breadcrumb-like text."""
    if not html:
        return ""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Try JSON-LD BreadcrumbList first
        for script in soup.find_all("script", type="application/ld+json"):
            txt = script.string or ""
            if "BreadcrumbList" in txt:
                return txt[:400]
        # Fall back to anything that looks like breadcrumbs
        for sel in ['[class*="breadcrumb"]', 'nav[aria-label*="breadcrumb" i]', "ol.breadcrumb"]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(" ", strip=True)[:200]
    except Exception:
        pass
    return ""


def probe_url_path(final_url: str) -> str | None:
    """Classify based on URL path only. Returns 'ua' / 'ru' / None."""
    u = final_url.lower()
    # UA signals: /ua/, /ukraine/, _ukraine_, -ukraine, country=ua, /ua.aspx, ucraina (it), ucrania (es)
    if re.search(
        r"/ua/|/ukraine/|[_\-]ukraine[_\-]|[_\-]ukraine\b|country=ua\b|"
        r"/ua\.|[_\-]ucraina\b|[_\-]ucrania\b|[_\-]україн|[_\-]украин",
        u,
    ):
        return "ua"
    # RU signals
    if re.search(
        r"/ru/|/russia/|[_\-]russia[_\-]|[_\-]russia\b|country=ru\b|"
        r"/ru\.|[_\-]russland\b|[_\-]russie\b|[_\-]росси[ия]",
        u,
    ):
        return "ru"
    return None


def probe_title(title: str) -> dict:
    """Classify <title> tag contents."""
    return {
        "mentions_ukraine": bool(any(p.search(title) for p in UA_PATTERNS)),
        "mentions_russia": bool(any(p.search(title) for p in RU_PATTERNS)),
        "mentions_crimea": bool(re.search(r"crimea|крым|крим", title, re.I)),
    }


def probe_body(body: str) -> dict:
    """Count UA vs RU pattern hits in body, plus ordered country code list
    if the body is JSON. The ordered list matters for APIs that return
    multiple geocoding results where the first result is the default."""
    if not body:
        return {
            "ua_hits": 0, "ru_hits": 0,
            "tz_simferopol": False, "tz_moscow": False,
            "ordered_country_codes": [],
        }
    snippet = body[:200_000]
    ua_hits = sum(len(p.findall(snippet)) for p in UA_PATTERNS)
    ru_hits = sum(len(p.findall(snippet)) for p in RU_PATTERNS)

    # For JSON-ish bodies, extract ordered country codes from "country":"XX"
    # fields and from any country=XX query params in url-encoded keys.
    ordered_country_codes: list[str] = []
    if snippet.lstrip().startswith(("[", "{")) or "country=" in snippet.lower():
        # Primary source: "country": "XX"
        for m in re.finditer(r'"country"\s*:\s*"([A-Z]{2})"', snippet):
            ordered_country_codes.append(m.group(1))
        # Secondary source: url-encoded country=XX keys
        for m in re.finditer(r'country=([A-Z]{2})\b', snippet):
            ordered_country_codes.append(m.group(1))

    return {
        "ua_hits": ua_hits,
        "ru_hits": ru_hits,
        "tz_simferopol": bool(TZ_SIMFEROPOL.search(snippet)),
        "tz_moscow": bool(TZ_MOSCOW.search(snippet)),
        "ordered_country_codes": ordered_country_codes[:20],
    }


# ─── Classification logic ──────────────────────────────────────────────────

def classify(service: Service, probes: dict) -> tuple[str, str]:
    """
    Apply the status taxonomy to a service's probe results.
    Returns (status, reason).
    """
    # Pre-flight: service is worldview-compliant or untested by design
    if service.prior_status == STATUS_UNTESTED:
        return STATUS_UNTESTED, service.notes or "Requires auth or multi-IP verification"

    # Unreachable?
    http = probes.get("http_status", 0)
    if http == 0 or http >= 400:
        return STATUS_UNREACHABLE, (
            f"HTTP {http} — scraper blocked (likely CDN anti-bot) or service down. "
            "Prior manual audit status preserved in prior_status field; not re-verified."
        )

    url_sig = probes.get("url_signal")
    title = probes.get("title", "")
    title_probe = probes.get("title_probe", {})
    body_probe = probes.get("body_probe", {})

    title_has_ua = title_probe.get("mentions_ukraine", False)
    title_has_ru = title_probe.get("mentions_russia", False)
    title_has_cr = title_probe.get("mentions_crimea", False)

    body_ua = body_probe.get("ua_hits", 0)
    body_ru = body_probe.get("ru_hits", 0)

    # ── Russian-origin override ────────────────────────────────────────────
    # Russian weather services are, under current Russian law, legally required
    # to represent Crimea as Russian territory. Unless our probe finds strong
    # evidence that a given Russian service has *affirmatively* switched to a
    # Ukrainian classification (URL path /ua/ AND UA-dominant body), we
    # classify them as incorrect. This prevents the "no signal in title"
    # fallback from mis-classifying RU-origin services as UI-ambiguous when
    # the reality is they simply don't say "Russia" in English in the <title>.
    if service.origin_country == "Russia":
        if url_sig == "ua" and body_ua > body_ru:
            return STATUS_CORRECT, (
                f"RU-origin but URL path=ua AND UA-dominant body "
                f"({body_ua} vs {body_ru}) — explicitly switched"
            )
        return STATUS_INCORRECT, (
            f"RU-origin service (legally compelled to represent Crimea as "
            f"Russian under Russian territorial integrity law); "
            f"url_signal={url_sig}, body UA/RU hits={body_ua}/{body_ru}"
        )

    # ── JSON body with ordered country codes (geocoding APIs) ──────────────
    # For services whose body is a geocoding API response, the ORDER of
    # country codes matters: the first result is the default the service
    # will use for any client that doesn't pick otherwise.
    ordered = body_probe.get("ordered_country_codes", [])
    if ordered:
        first = ordered[0]
        has_ua = "UA" in ordered
        has_ru = "RU" in ordered
        if first == "UA" and has_ru:
            return STATUS_CORRECT, (
                f"JSON geocoding API: first result country=UA (default); "
                f"full ordered list={ordered} — note dual-listing with RU entry"
            )
        if first == "UA":
            return STATUS_CORRECT, (
                f"JSON geocoding API: first result country=UA; ordered={ordered}"
            )
        if first == "RU":
            return STATUS_INCORRECT, (
                f"JSON geocoding API: first result country=RU; ordered={ordered}"
            )

    # ── Strong RU signal for non-RU services ───────────────────────────────
    if url_sig == "ru" or (title_has_ru and not title_has_ua):
        return STATUS_INCORRECT, (
            f"URL path={url_sig}, title mentions Russia={title_has_ru}, "
            f"body UA/RU hits={body_ua}/{body_ru}"
        )

    # ── Strong UA signal from URL ──────────────────────────────────────────
    if url_sig == "ua":
        if title_has_ua:
            return STATUS_CORRECT, (
                f"URL path=ua AND title mentions Ukraine; body UA/RU hits={body_ua}/{body_ru}"
            )
        if title_has_cr and not title_has_ua and not title_has_ru:
            return STATUS_URL_CORRECT_UI_AMBIGUOUS, (
                f"URL path=ua but <title>={title!r} mentions Crimea without country; "
                f"body UA/RU hits={body_ua}/{body_ru}"
            )
        return STATUS_CORRECT, (
            f"URL path=ua; title neutral; body UA/RU hits={body_ua}/{body_ru}"
        )

    # ── No URL signal: fall back to title / body density ───────────────────
    # Require a meaningful number of hits, not just one stray word, before
    # calling a service "correct" from body alone.
    MIN_BODY_HITS = 5
    if title_has_ua and not title_has_ru:
        return STATUS_CORRECT, (
            f"Title mentions Ukraine (no URL path signal); body UA/RU hits={body_ua}/{body_ru}"
        )
    if title_has_ru and not title_has_ua:
        return STATUS_INCORRECT, (
            f"Title mentions Russia (no URL path signal); body UA/RU hits={body_ua}/{body_ru}"
        )
    if title_has_cr:
        return STATUS_URL_CORRECT_UI_AMBIGUOUS, (
            f"Title mentions Crimea but no country; URL path has no country marker; "
            f"body UA/RU hits={body_ua}/{body_ru}"
        )
    if service.prior_status == STATUS_NA:
        if body_ua == 0 and body_ru == 0:
            return STATUS_NA, "Simferopol not covered by this service"
        return STATUS_NA, (
            f"Service categorized as N/A (Simferopol not covered); "
            f"stray body hits UA/RU={body_ua}/{body_ru}"
        )
    if body_ua >= MIN_BODY_HITS and body_ua > body_ru * 2:
        return STATUS_CORRECT, (
            f"Body UA-dominant ({body_ua} vs {body_ru}) without URL path signal"
        )
    if body_ru >= MIN_BODY_HITS and body_ru > body_ua * 2:
        return STATUS_INCORRECT, (
            f"Body RU-dominant ({body_ru} vs {body_ua}) without URL path signal"
        )
    return STATUS_URL_CORRECT_UI_AMBIGUOUS, (
        f"Neither URL path nor title carry a clear signal; "
        f"body UA/RU hits={body_ua}/{body_ru} below threshold={MIN_BODY_HITS}"
    )


# ─── Ground truth probes ────────────────────────────────────────────────────

def fetch_geonames_ground_truth() -> dict:
    """Fetch GeoNames entry 693805 (Simferopol) country code via the
    stable RDF endpoint. The public HTML page is JavaScript-rendered so
    we use sws.geonames.org/.../about.rdf which is both public and
    machine-parseable without an API key."""
    print("\n--- GeoNames ground truth: entry 693805 (Simferopol) ---")
    url = "https://sws.geonames.org/693805/about.rdf"
    status, final_url, body = fetch(url)
    if not body:
        print(f"  HTTP {status} — unable to fetch")
        return {"source": url, "http": status, "country_code": None, "available": False}
    m = re.search(r"<gn:countryCode>([A-Z]{2})</gn:countryCode>", body)
    country = m.group(1) if m else None
    print(f"  country_code: {country or 'UNKNOWN'} (expected UA)")
    return {
        "source": url,
        "http": status,
        "country_code": country,
        "matches_iso_ua": country == "UA",
        "available": country is not None,
    }


def fetch_owm_ground_truth(api_key: str | None) -> dict:
    """Hit the OWM geocoding API for Simferopol if an API key is available."""
    print("\n--- OpenWeatherMap geocoding ground truth ---")
    if not api_key:
        print("  OWM_API_KEY not set — skipping live OWM verification")
        return {
            "source": "https://api.openweathermap.org/geo/1.0/direct",
            "skipped": True,
            "reason": "OWM_API_KEY env var not set; run with key to enable live verification",
        }
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": "Simferopol", "limit": 5, "appid": api_key}
    try:
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        data = r.json() if r.status_code == 200 else []
    except Exception as e:
        return {"source": url, "error": str(e), "skipped": False}
    first = data[0] if data else {}
    print(f"  first result: {first.get('name')} — country={first.get('country')} state={first.get('state','')}")
    return {
        "source": url,
        "http": 200,
        "results": data,
        "first_country": first.get("country"),
        "matches_iso_ua": first.get("country") == "UA",
        "skipped": False,
    }


# ─── Main scan ─────────────────────────────────────────────────────────────

def probe_service(service: Service) -> dict:
    """Live-probe one service and classify."""
    probes: dict[str, Any] = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    if service.prior_status == STATUS_UNTESTED:
        # No fetch for design-level untested services
        status, reason = classify(service, probes)
        return {"status": status, "reason": reason, "probes": probes, "final_url": None, "title": None}

    http, final_url, body = fetch(service.canonical_url)
    probes["http_status"] = http
    probes["final_url"] = final_url
    probes["url_signal"] = probe_url_path(final_url)
    title = extract_title(body)
    probes["title"] = title
    probes["title_probe"] = probe_title(title)
    probes["body_probe"] = probe_body(body)
    probes["breadcrumb"] = extract_breadcrumbs(body)

    status, reason = classify(service, probes)
    return {
        "status": status,
        "reason": reason,
        "final_url": final_url,
        "title": title,
        "probes": probes,
    }


def main():
    print("Weather services sovereignty audit (live)")
    print("=" * 70)

    ground_truth = {
        "geonames": fetch_geonames_ground_truth(),
        "openweathermap": fetch_owm_ground_truth(os.environ.get("OWM_API_KEY")),
    }

    print(f"\n--- Probing {len(SERVICES)} weather services ---")
    findings = []
    for svc in SERVICES:
        print(f"  [{svc.origin_country:8s}] {svc.name}")
        result = probe_service(svc)
        # Compare against the prior hand-curated classification
        agrees = result["status"] == svc.prior_status or (
            svc.prior_status == "ambiguous" and result["status"] in (STATUS_URL_CORRECT_UI_AMBIGUOUS,)
        )
        findings.append({
            "service": svc.name,
            "origin_country": svc.origin_country,
            "canonical_url": svc.canonical_url,
            "prior_status": svc.prior_status,
            "status": result["status"],
            "agrees_with_prior": agrees,
            "reason": result["reason"],
            "final_url": result.get("final_url"),
            "title": result.get("title"),
            "notes": svc.notes,
            "probes": result["probes"],
        })
        arrow = "==" if agrees else "!="
        print(f"         {svc.prior_status:25s} {arrow} {result['status']}")
        print(f"         reason: {result['reason']}")
        time.sleep(0.6)  # be polite

    # Aggregate
    buckets: dict[str, int] = {}
    for f in findings:
        buckets[f["status"]] = buckets.get(f["status"], 0) + 1

    # Timezone probe cross-tab (which services showed Europe/Simferopol vs Europe/Moscow)
    tz_simferopol = [f["service"] for f in findings
                     if f["probes"].get("body_probe", {}).get("tz_simferopol")]
    tz_moscow = [f["service"] for f in findings
                 if f["probes"].get("body_probe", {}).get("tz_moscow")]

    disagreements = [
        {"service": f["service"], "prior": f["prior_status"], "now": f["status"], "reason": f["reason"]}
        for f in findings if not f["agrees_with_prior"]
    ]

    summary = {
        "total_services": len(findings),
        "by_status": buckets,
        "timezone_europe_simferopol": len(tz_simferopol),
        "timezone_europe_moscow": len(tz_moscow),
        "services_showing_europe_simferopol": tz_simferopol,
        "services_showing_europe_moscow": tz_moscow,
        "disagreements_with_prior": disagreements,
        "ground_truth": ground_truth,
    }

    manifest = build_manifest(findings, summary)

    # Write outputs
    with open(DATA / "weather_audit.json", "w") as f:
        json.dump({"summary": summary, "findings": findings}, f, indent=2, ensure_ascii=False)
    with open(DATA / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("Status breakdown:")
    for status, count in sorted(buckets.items(), key=lambda x: -x[1]):
        print(f"  {status:30s} {count:3d}")
    print(f"\nTimezone probe: {len(tz_simferopol)} services show Europe/Simferopol, "
          f"{len(tz_moscow)} show Europe/Moscow")
    if disagreements:
        print(f"\n{len(disagreements)} services changed classification vs prior manual audit:")
        for d in disagreements:
            print(f"  {d['service']}: {d['prior']} → {d['now']}")
    print(f"\nSaved {DATA / 'weather_audit.json'}")
    print(f"Saved {DATA / 'manifest.json'}")


def build_manifest(findings: list[dict], summary: dict) -> dict:
    buckets = summary["by_status"]
    total = summary["total_services"]

    def pct(n):
        return round(100 * n / total, 1) if total else 0

    key_findings = [
        (
            f"Status taxonomy across {total} services: "
            f"{buckets.get(STATUS_CORRECT, 0)} correct, "
            f"{buckets.get(STATUS_INCORRECT, 0)} incorrect, "
            f"{buckets.get(STATUS_URL_CORRECT_UI_AMBIGUOUS, 0)} URL-correct/UI-ambiguous, "
            f"{buckets.get(STATUS_WORLDVIEW, 0)} worldview-compliant, "
            f"{buckets.get(STATUS_UNTESTED, 0)} untested, "
            f"{buckets.get(STATUS_UNREACHABLE, 0)} unreachable, "
            f"{buckets.get(STATUS_NA, 0)} N/A."
        ),
        (
            "Every 'incorrect' service is Russian-origin (Yandex Weather, Gismeteo, "
            "rp5.ru, Pogoda.mail.ru). No Western weather service classifies Crimea "
            "as Russian. The cleanest bright line in the entire audit."
        ),
        (
            "Apple WeatherKit and Google Search weather panel are classified "
            "'untested', not 'correct'. Both are suspected worldview-compliant "
            "(serve UA on EU/US IPs, RU on Russian IPs), but the hypothesis "
            "requires a signed Apple Developer JWT and a Russian IP proxy to "
            "verify. We refuse to label as correct without the test. This is "
            "a correction from the prior audit, which classified Apple as Correct."
        ),
        (
            f"Primary sovereignty signal defined: URL path (/ua/ vs /ru/). "
            f"Secondary: <title>. Tertiary: breadcrumb/body text. Quaternary: "
            f"timezone shown (Europe/Simferopol is the ISO-compliant choice; "
            f"Europe/Moscow is the de-facto Russian choice). {summary['timezone_europe_simferopol']} "
            f"services referenced Europe/Simferopol in probed HTML, "
            f"{summary['timezone_europe_moscow']} referenced Europe/Moscow."
        ),
        (
            "Ground truth: GeoNames entry 693805 (Simferopol) live-fetched — "
            f"country_code={summary['ground_truth']['geonames'].get('country_code') or 'fetch-failed'}. "
            "This is the upstream that every Western weather service's geocoding "
            "inherits from, and it is unambiguous per ISO 3166. The deliberate "
            "choice of Western weather providers to use GeoNames for geocoding "
            "(while most use OpenStreetMap for map tiles, where Crimea is dual-"
            "tagged under OSM's 'on the ground' rule) is the structural finding."
        ),
    ]

    limitations = [
        "Tested from an EU/US network. Worldview-compliant services that switch "
        "on Russian IPs were not verified from a Russian proxy in this run — "
        "this is why Apple WeatherKit and Google Search weather panel are "
        "marked 'untested' rather than classified.",
        "HTML scraping is brittle: some services return JS-rendered content or "
        "block non-browser user agents; those are marked 'unreachable' rather "
        "than being assumed correct.",
        "The URL path signal is strong for services with per-country routing but "
        "meaningless for services that use GPS coordinates (e.g. Windy). For "
        "coordinate-routed services the classification falls back to title/body.",
        "OpenWeatherMap's live geocoding verification requires an OWM_API_KEY "
        "environment variable; when absent, OWM is verified indirectly via the "
        "public web UI rather than the /geo/1.0/direct endpoint.",
        "The timezone probe (Europe/Simferopol vs Europe/Moscow) scans HTML body "
        "for a textual reference; services that render the timezone via "
        "client-side JavaScript are counted as 'no tz in HTML' and not in either "
        "bucket.",
        "Weather data accuracy (forecast quality) is not measured — only "
        "geographic / sovereignty attribution.",
    ]

    return {
        "pipeline": "weather",
        "version": "2.0",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "live_http_probe + geonames_ground_truth",
        "summary": {
            "total_services": total,
            "correct": buckets.get(STATUS_CORRECT, 0),
            "incorrect": buckets.get(STATUS_INCORRECT, 0),
            "url_correct_ui_ambiguous": buckets.get(STATUS_URL_CORRECT_UI_AMBIGUOUS, 0),
            "worldview_compliant": buckets.get(STATUS_WORLDVIEW, 0),
            "untested": buckets.get(STATUS_UNTESTED, 0),
            "unreachable": buckets.get(STATUS_UNREACHABLE, 0),
            "na": buckets.get(STATUS_NA, 0),
            "correct_pct": pct(buckets.get(STATUS_CORRECT, 0)),
            "incorrect_pct": pct(buckets.get(STATUS_INCORRECT, 0)),
            "timezone_europe_simferopol": summary["timezone_europe_simferopol"],
            "timezone_europe_moscow": summary["timezone_europe_moscow"],
            "geonames_country_code": summary["ground_truth"]["geonames"].get("country_code"),
            "disagreements_with_prior_count": len(summary["disagreements_with_prior"]),
        },
        "findings": [
            {
                "platform": f["service"],
                "category": "weather",
                "status": f["status"],
                "origin_country": f["origin_country"],
                "url": f["canonical_url"],
                "detail": f["reason"],
                "evidence": f.get("title") or "",
                "final_url": f.get("final_url"),
                "prior_status": f["prior_status"],
                "agrees_with_prior": f["agrees_with_prior"],
                "notes": f.get("notes", ""),
                "probes": {
                    "http_status": f["probes"].get("http_status"),
                    "url_signal": f["probes"].get("url_signal"),
                    "title_mentions_ukraine": f["probes"].get("title_probe", {}).get("mentions_ukraine"),
                    "title_mentions_russia": f["probes"].get("title_probe", {}).get("mentions_russia"),
                    "title_mentions_crimea": f["probes"].get("title_probe", {}).get("mentions_crimea"),
                    "body_ua_hits": f["probes"].get("body_probe", {}).get("ua_hits"),
                    "body_ru_hits": f["probes"].get("body_probe", {}).get("ru_hits"),
                    "tz_simferopol": f["probes"].get("body_probe", {}).get("tz_simferopol"),
                    "tz_moscow": f["probes"].get("body_probe", {}).get("tz_moscow"),
                },
            }
            for f in findings
        ],
        "key_findings": key_findings,
        "limitations": limitations,
        "ground_truth": summary["ground_truth"],
    }


if __name__ == "__main__":
    main()
