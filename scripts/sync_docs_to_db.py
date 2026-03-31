"""
Sync documented findings from markdown reports into the JSON database.

The background research agents wrote rich docs (maps.md, weather.md, travel.md,
social_media.md) but those findings aren't in platforms.json. This script
adds them to ensure the structured database matches the documentation.

Usage:
    python scripts/sync_docs_to_db.py
"""

from audit_framework import (
    AuditDatabase,
    AuditMethod,
    PlatformCategory,
    SovereigntyStatus,
    create_finding,
)


def sync_map_services(db: AuditDatabase):
    """Add map service findings from docs/maps.md."""
    print("--- Syncing Map Services ---")

    findings = [
        create_finding(
            platform="Google Maps",
            category=PlatformCategory.MAP_SERVICE,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "Geo-dependent borders: solid international border (Russia) from "
                "Russia, light internal border (Ukraine) from Ukraine, dashed "
                "'disputed' border from all other countries. No policy change "
                "since 2014. The 'disputed' framing is itself problematic — "
                "UNGA Res 68/262 affirmed Crimea as Ukrainian."
            ),
            url="https://maps.google.com/",
            evidence=(
                "Google: 'In countries where we have a localized version, "
                "we follow local laws on representing borders.'"
            ),
            notes="30+ localized map versions exist.",
        ),
        create_finding(
            platform="Apple Maps",
            category=PlatformCategory.MAP_SERVICE,
            status=SovereigntyStatus.CORRECT,
            method=AuditMethod.MANUAL,
            detail=(
                "Shows Crimea as part of Ukraine outside Russia since March "
                "2022. From Russia: shows as part of Russia (per Russian law). "
                "Apple ceased operations in Russia, so RU version may no longer "
                "be maintained. Best major map service for Crimea."
            ),
            url="https://maps.apple.com/",
            evidence=(
                "AppleInsider (2022-03-04): 'Apple Maps now shows Crimea as "
                "part of Ukraine'. Ukrainer Stop Mapaganda (2023): 'Apple Maps "
                "shows Ukraine's borders correctly.'"
            ),
        ),
        create_finding(
            platform="Bing Maps (Microsoft)",
            category=PlatformCategory.MAP_SERVICE,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "Insufficient public documentation for 2025-2026 state. "
                "Historically showed dashed border similar to Google. "
                "Needs direct VPN-based verification."
            ),
            url="https://www.bing.com/maps",
            notes="Requires manual verification with VPN.",
        ),
        create_finding(
            platform="OpenStreetMap",
            category=PlatformCategory.MAP_SERVICE,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "Dual mapping: Crimea simultaneously in both Ukraine and Russia "
                "administrative hierarchies since 2014. 'On the ground' rule "
                "creates ambiguity. Nominatim geocoder returns Ukraine. Rendered "
                "maps vary by tile provider."
            ),
            url="https://wiki.openstreetmap.org/wiki/WikiProject_Crimea",
            evidence="WikiProject Crimea documents the dual-mapping policy.",
        ),
        create_finding(
            platform="National Geographic",
            category=PlatformCategory.MAP_SERVICE,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "Inconsistent: five different representations across products. "
                "Europe Wall Map labels Crimea as Russian. Other products show "
                "disputed borders. No single policy."
            ),
            url="https://www.nationalgeographic.com/",
            evidence=(
                "NatGeo 2014 article: 'How Should Crimea Be Shown?' describes "
                "internal debate."
            ),
        ),
    ]

    for f in findings:
        db.add(f)
        print(f"  Added: {f['platform']}")


def sync_weather_services(db: AuditDatabase):
    """Add weather service findings from docs/weather.md."""
    print("\n--- Syncing Weather Services ---")

    services = [
        ("AccuWeather", SovereigntyStatus.CORRECT,
         "Simferopol listed as 'Simferopol, Crimea, Ukraine'. "
         "URL path contains /ua/ country code.",
         "https://www.accuweather.com/en/ua/simferopol/322464/weather-forecast/322464"),
        ("Weather Underground", SovereigntyStatus.CORRECT,
         "Simferopol listed under Ukraine. URL path /ua/.",
         "https://www.wunderground.com/forecast/ua/simferopol"),
        ("TimeAndDate.com", SovereigntyStatus.CORRECT,
         "Simferopol listed as 'Simferopol, Ukraine'.",
         "https://www.timeanddate.com/weather/ukraine/simferopol"),
        ("Weather Spark", SovereigntyStatus.CORRECT,
         "Lists 'Average Weather in Simferopol Ukraine'.",
         "https://weatherspark.com/y/98362/Average-Weather-in-Simferopol-Ukraine"),
        ("Meteoblue", SovereigntyStatus.CORRECT,
         "Simferopol listed under Ukraine.",
         "https://www.meteoblue.com/en/weather/week/simferopol_ukraine_693805"),
        ("Weather-Forecast.com", SovereigntyStatus.CORRECT,
         "Simferopol listed under Ukraine.",
         "https://www.weather-forecast.com/locations/Simferopol"),
        ("Ventusky", SovereigntyStatus.CORRECT,
         "Simferopol listed under Ukraine.",
         "https://www.ventusky.com/?p=44.95;34.10"),
        ("Weather Atlas", SovereigntyStatus.CORRECT,
         "Simferopol climate data listed under Ukraine.",
         "https://www.weather-atlas.com/en/ukraine/simferopol-climate"),
    ]

    for name, status, detail, url in services:
        db.add(create_finding(
            platform=name,
            category=PlatformCategory.WEATHER,
            status=status,
            method=AuditMethod.AUTOMATED_API,
            detail=detail,
            url=url,
            notes=(
                "Weather services rely on GeoNames and ISO 3166, which "
                "classify Crimea under Ukraine."
            ),
        ))
        print(f"  Added: {name}")


def sync_travel_platforms(db: AuditDatabase):
    """Add travel platform findings from docs/travel.md."""
    print("\n--- Syncing Travel Platforms ---")

    findings = [
        create_finding(
            platform="Booking.com",
            category=PlatformCategory.TRAVEL,
            status=SovereigntyStatus.BLOCKED,
            method=AuditMethod.MANUAL,
            detail=(
                "Suspended all Russia and Crimea operations since 2022 due to "
                "EU/US sanctions. No Crimea properties bookable."
            ),
            url="https://www.booking.com/",
            notes="EU sanctions on Crimea renewed through June 23, 2026.",
        ),
        create_finding(
            platform="Airbnb",
            category=PlatformCategory.TRAVEL,
            status=SovereigntyStatus.BLOCKED,
            method=AuditMethod.MANUAL,
            detail=(
                "Explicitly blocks all Crimea listings per sanctions policy. "
                "Announced 2022: 'suspended all operations in Russia and Belarus'."
            ),
            url="https://news.airbnb.com/airbnbs-actions-in-response-to-the-ukraine-crisis/",
        ),
        create_finding(
            platform="Expedia / Hotels.com",
            category=PlatformCategory.TRAVEL,
            status=SovereigntyStatus.BLOCKED,
            method=AuditMethod.MANUAL,
            detail="Ceased all Russia travel sales in 2022.",
            url="https://www.expedia.com/",
        ),
        create_finding(
            platform="Google Flights (SIP airport)",
            category=PlatformCategory.TRAVEL,
            status=SovereigntyStatus.CORRECT,
            method=AuditMethod.AUTOMATED_DATA,
            detail=(
                "SIP (Simferopol) airport classified under Ukraine. ICAO: UKFF "
                "(UK=Ukraine prefix). Alt ICAO: URFF (UR=Russia). All flights "
                "suspended since Feb 2022."
            ),
            url="https://www.google.com/travel/flights",
            evidence="OurAirports data: country=UA, region=UA-43",
        ),
        create_finding(
            platform="TripAdvisor",
            category=PlatformCategory.TRAVEL,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "Lists Crimea under 'Europe' with NO country designation — "
                "neither Ukraine nor Russia. Avoids the sovereignty question "
                "entirely."
            ),
            url="https://www.tripadvisor.com/Tourism-g313972-Crimea-Vacations.html",
            notes="Evasion is less harmful than 'Russia' but still fails to "
                  "reflect internationally recognized status.",
        ),
        create_finding(
            platform="Skyscanner (SIP airport)",
            category=PlatformCategory.TRAVEL,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.AUTOMATED_API,
            detail=(
                "SIP airport page accessible but country classification unclear "
                "from HTML. Airport suspended — no active flights."
            ),
            url="https://www.skyscanner.com/transport/flights/sip/",
        ),
    ]

    for f in findings:
        db.add(f)
        print(f"  Added: {f['platform']}")


def sync_social_media(db: AuditDatabase):
    """Add social media findings from docs/social_media.md."""
    print("\n--- Syncing Social Media ---")

    findings = [
        create_finding(
            platform="Instagram",
            category=PlatformCategory.SOCIAL_MEDIA,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.MANUAL,
            detail=(
                "Maintains BOTH 'Crimea, Ukraine' and 'Russia, Crimea, Yalta' "
                "as active location tags. Users can freely choose either, "
                "effectively normalizing Russia's sovereignty claim."
            ),
            url="https://www.instagram.com/",
            notes="Dual tags allow users to label the same location under "
                  "either country.",
        ),
        create_finding(
            platform="TikTok",
            category=PlatformCategory.SOCIAL_MEDIA,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "Moved Ukraine out of shared 'Russia + Ukraine' region category "
                "in 2022 after Ukraine's Ministry of Digital Transformation "
                "intervened. Crimea-specific city tags need verification."
            ),
            url="https://imi.org.ua/en/news/tiktok-moves-ukraine-from-shared-region-with-russia-ministry-of-digital-transformation-i46927",
        ),
        create_finding(
            platform="Facebook",
            category=PlatformCategory.SOCIAL_MEDIA,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "Likely shares Instagram's location database (both Meta). "
                "May have contradictory location tags. Needs direct verification."
            ),
            url="https://www.facebook.com/",
            notes="Placeholder — needs manual check.",
        ),
        create_finding(
            platform="X / Twitter",
            category=PlatformCategory.SOCIAL_MEDIA,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.MANUAL,
            detail=(
                "No structured country enforcement on location tags. Users "
                "can set free-text locations. Needs verification of any "
                "location autocomplete behavior for Crimean cities."
            ),
            url="https://x.com/",
            notes="Placeholder — needs manual check.",
        ),
    ]

    for f in findings:
        db.add(f)
        print(f"  Added: {f['platform']}")


def sync_reference_platforms(db: AuditDatabase):
    """Add missing reference platform findings."""
    print("\n--- Syncing Reference Platforms ---")

    # Add French Wikipedia (was missing)
    db.add(create_finding(
        platform="Wikipedia (French)",
        category=PlatformCategory.REFERENCE,
        status=SovereigntyStatus.AMBIGUOUS,
        method=AuditMethod.AUTOMATED_API,
        detail=(
            "Geographic description mentioning both Ukraine and Russia. "
            "Does not lead with sovereignty statement."
        ),
        url="https://fr.wikipedia.org/wiki/Crim%C3%A9e",
        evidence=(
            "La Crimée est une péninsule d'Europe de l'Est, située au sud "
            "de l'oblast de Kherson en Ukraine..."
        ),
    ))
    print("  Added: Wikipedia (French)")


def sync_open_source_extras(db: AuditDatabase):
    """Add open source findings from enriched docs/open_source.md."""
    print("\n--- Syncing Open Source Extras ---")

    extras = [
        create_finding(
            platform="GeoPandas (naturalearth_lowres)",
            category=PlatformCategory.DATA_VIZ,
            status=SovereigntyStatus.CORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Was incorrect until v0.12.2 (2022). GitHub issue #2382 reported "
                "Crimea shown as Russian. PR #2670 fixed it. Datasets module "
                "deprecated and removed in v1.0 (2024). ~15M monthly PyPI "
                "downloads. Legacy versions still propagate error."
            ),
            url="https://github.com/geopandas/geopandas/issues/2382",
            notes="Fixed upstream but legacy tutorials still show incorrect maps.",
        ),
        create_finding(
            platform="Cartopy (SciTools)",
            category=PlatformCategory.DATA_VIZ,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Downloads Natural Earth at runtime. Default 1:110m scale assigns "
                "Crimea to Russia. No POV option exposed. Used in climate science, "
                "meteorology, earth sciences. ~2-3M monthly PyPI downloads. "
                "No issue filed yet."
            ),
            url="https://github.com/SciTools/cartopy",
        ),
        create_finding(
            platform="rnaturalearth (R package)",
            category=PlatformCategory.DATA_VIZ,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Issue #116 requested fix — maintainer refused: 'We do not modify "
                "the underlying data.' Issue #27 similarly declined. Users must "
                "manually modify geometries with sf package. 50-100K monthly CRAN "
                "downloads."
            ),
            url="https://github.com/ropensci/rnaturalearth/issues/116",
            notes="Maintainers explicitly declined to fix.",
        ),
        create_finding(
            platform="spData (R, 'Geocomputation with R')",
            category=PlatformCategory.DATA_VIZ,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Issue #50 'Improper map of Ukraine' — Crimea shown as Russian. "
                "Sourced from rnaturalearth. Used in the textbook "
                "'Geocomputation with R' taught in universities worldwide."
            ),
            url="https://github.com/Nowosad/spData/issues/50",
        ),
        create_finding(
            platform="moment-timezone (npm)",
            category=PlatformCategory.TECH_INFRA,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Issue #954 requested dissociating Europe/Simferopol from RU. "
                "Closed without change. Maintainer: 'We directly consume IANA "
                "data. No extra decision layer.' ~12M weekly npm downloads."
            ),
            url="https://github.com/moment/moment-timezone/issues/954",
        ),
        create_finding(
            platform="libphonenumber-js (npm)",
            category=PlatformCategory.TECH_INFRA,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Reimplementation of Google libphonenumber. +7-365/978 (Crimean) "
                "numbers parsed as RU. ~13.6M weekly npm downloads. Combined "
                "with google-libphonenumber wrapper (~1.6M/wk), total phone "
                "number library impact is ~15.2M weekly downloads."
            ),
            url="https://www.npmjs.com/package/libphonenumber-js",
        ),
        create_finding(
            platform="MaxMind GeoIP2",
            category=PlatformCategory.IP_GEOLOCATION,
            status=SovereigntyStatus.CORRECT,
            method=AuditMethod.AUTOMATED_DATA,
            detail=(
                "Industry-standard IP geolocation. Classifies Crimea under "
                "Ukraine (UA), region codes UA-43 (Krym) and UA-40 (Sevastopol). "
                "Data source: GeoNames. ~96% accuracy for Crimean visitors."
            ),
            url="https://dev.maxmind.com/release-note/geoip-accuracy-in-crimea/",
        ),
        create_finding(
            platform="GeoNames",
            category=PlatformCategory.REFERENCE,
            status=SovereigntyStatus.CORRECT,
            method=AuditMethod.AUTOMATED_DATA,
            detail=(
                "Major open geographic database. Lists Crimea in Ukraine's "
                "administrative hierarchy. Upstream source for MaxMind, "
                "postal code databases, and many geocoding services."
            ),
            url="https://www.geonames.org/UA/administrative-division-ukraine.html",
        ),
        create_finding(
            platform="Google libaddressinput",
            category=PlatformCategory.TECH_INFRA,
            status=SovereigntyStatus.CORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Google's address validation library (615 stars). Classifies "
                "Crimean addresses under UA (Ukraine). Powers address forms in "
                "Android apps and Chrome autofill."
            ),
            url="https://github.com/google/libaddressinput",
        ),
        create_finding(
            platform="iso3166-2-db (esosedi/3166)",
            category=PlatformCategory.OPEN_SOURCE,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "Default mode includes Crimea as part of Russia. Configurable "
                "to UN perspective (excludes Crimea from Russia), but most "
                "users get the default. ~10K weekly npm downloads."
            ),
            url="https://github.com/esosedi/3166",
            notes="Could change default to UN perspective.",
        ),
        create_finding(
            platform="mledoze/countries (GitHub, 6.2K stars)",
            category=PlatformCategory.OPEN_SOURCE,
            status=SovereigntyStatus.AMBIGUOUS,
            method=AuditMethod.SOURCE_CODE,
            detail=(
                "One of the most popular country data repos. GeoJSON boundaries "
                "likely derived from Natural Earth. Crimea handling not "
                "explicitly documented. Needs boundary inspection."
            ),
            url="https://github.com/mledoze/countries",
        ),
        create_finding(
            platform="Postal code databases (Russian Post)",
            category=PlatformCategory.TECH_INFRA,
            status=SovereigntyStatus.INCORRECT,
            method=AuditMethod.AUTOMATED_DATA,
            detail=(
                "Russia assigned postal codes 295000-299999 to Crimea post-2014. "
                "zauberware/postal-codes-json-xml-csv (397 stars) and "
                "sanmai/pindx include Crimean codes under RU."
            ),
            url="https://github.com/zauberware/postal-codes-json-xml-csv",
            notes="Reflects Russian Post operational reality.",
        ),
    ]

    for f in extras:
        db.add(f)
        print(f"  Added: {f['platform']}")


def main():
    db = AuditDatabase()
    initial = len(db.data["findings"])

    sync_map_services(db)
    sync_weather_services(db)
    sync_travel_platforms(db)
    sync_social_media(db)
    sync_reference_platforms(db)
    sync_open_source_extras(db)

    db.save()
    final = len(db.data["findings"])
    print(f"\n{'='*50}")
    print(f"Synced: {initial} -> {final} findings (+{final - initial})")
    print(f"Database saved to: {db.path}")


if __name__ == "__main__":
    main()
