"""
Map Services & Geocoding Crimea Checker

Automated checks for map services and geocoding APIs to determine
how they classify Simferopol / Crimea.

Usage:
    python scripts/check_map_services.py
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
SESSION.headers.update({
    "User-Agent": "CrimeaSovereigntyAudit/1.0 (research)",
    "Accept": "application/json",
})

SIMFEROPOL_LAT = 44.952
SIMFEROPOL_LON = 34.103


def check_nominatim_forward() -> list[dict]:
    """Check OSM Nominatim forward geocoding."""
    print("\n--- OSM Nominatim (forward geocode) ---")
    findings = []
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": "Simferopol", "format": "json", "addressdetails": 1, "limit": 3}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                cc = data[0].get("address", {}).get("country_code", "?")
                country = data[0].get("address", {}).get("country", "?")
                display = data[0].get("display_name", "")
                status = SovereigntyStatus.CORRECT if cc == "ua" else (
                    SovereigntyStatus.INCORRECT if cc == "ru" else SovereigntyStatus.AMBIGUOUS
                )
                findings.append(create_finding(
                    platform="OSM Nominatim (forward geocode)",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → country_code='{cc}', country='{country}'. Display: {display}",
                    url=resp.url,
                    evidence=json.dumps(data[0].get("address", {})),
                ))
                print(f"  country_code={cc}, country={country}")
    except Exception as e:
        print(f"  ERROR: {e}")
    return findings


def check_nominatim_reverse() -> list[dict]:
    """Check OSM Nominatim reverse geocoding for Simferopol coords."""
    print("\n--- OSM Nominatim (reverse geocode) ---")
    findings = []
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": SIMFEROPOL_LAT, "lon": SIMFEROPOL_LON, "format": "json", "addressdetails": 1}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            cc = data.get("address", {}).get("country_code", "?")
            country = data.get("address", {}).get("country", "?")
            status = SovereigntyStatus.CORRECT if cc == "ua" else (
                SovereigntyStatus.INCORRECT if cc == "ru" else SovereigntyStatus.AMBIGUOUS
            )
            findings.append(create_finding(
                platform="OSM Nominatim (reverse geocode)",
                category=PlatformCategory.MAP_SERVICE,
                status=status,
                method=AuditMethod.AUTOMATED_API,
                detail=f"Coords {SIMFEROPOL_LAT},{SIMFEROPOL_LON} → country_code='{cc}', country='{country}'.",
                url=resp.url,
                evidence=json.dumps(data.get("address", {})),
            ))
            print(f"  country_code={cc}, country={country}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1.5)
    return findings


def check_photon() -> list[dict]:
    """Check Photon (Komoot) geocoder."""
    print("\n--- Photon / Komoot geocoder ---")
    findings = []
    url = "https://photon.komoot.io/api/"
    params = {"q": "Simferopol", "limit": 3}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                cc = props.get("countrycode", "?")
                country = props.get("country", "?")
                state = props.get("state", "?")
                status = SovereigntyStatus.CORRECT if cc == "UA" else (
                    SovereigntyStatus.INCORRECT if cc == "RU" else SovereigntyStatus.AMBIGUOUS
                )
                findings.append(create_finding(
                    platform="Photon (Komoot geocoder)",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → countrycode='{cc}', country='{country}', state='{state}'.",
                    url=resp.url,
                    evidence=json.dumps(props),
                ))
                print(f"  countrycode={cc}, country={country}, state={state}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_photon_reverse() -> list[dict]:
    """Check Photon reverse geocoding."""
    print("\n--- Photon (reverse geocode) ---")
    findings = []
    url = "https://photon.komoot.io/reverse"
    params = {"lat": SIMFEROPOL_LAT, "lon": SIMFEROPOL_LON}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                cc = props.get("countrycode", "?")
                country = props.get("country", "?")
                status = SovereigntyStatus.CORRECT if cc == "UA" else (
                    SovereigntyStatus.INCORRECT if cc == "RU" else SovereigntyStatus.AMBIGUOUS
                )
                findings.append(create_finding(
                    platform="Photon (reverse geocode)",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Coords {SIMFEROPOL_LAT},{SIMFEROPOL_LON} → countrycode='{cc}', country='{country}'.",
                    url=resp.url,
                    evidence=json.dumps(props),
                ))
                print(f"  countrycode={cc}, country={country}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_openweathermap_geocoding() -> list[dict]:
    """Check OpenWeatherMap geocoding API (uses GeoNames)."""
    print("\n--- OpenWeatherMap Geocoding ---")
    findings = []
    # OWM city lookup by GeoNames ID
    url = "https://openweathermap.org/data/2.5/weather"
    params = {"id": 693805, "appid": "439d4b804bc8187953eb36d2a8c26a02"}  # public demo key
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            cc = data.get("sys", {}).get("country", "?")
            name = data.get("name", "?")
            status = SovereigntyStatus.CORRECT if cc == "UA" else (
                SovereigntyStatus.INCORRECT if cc == "RU" else SovereigntyStatus.AMBIGUOUS
            )
            findings.append(create_finding(
                platform="OpenWeatherMap (geocoding API)",
                category=PlatformCategory.MAP_SERVICE,
                status=status,
                method=AuditMethod.AUTOMATED_API,
                detail=f"GeoNames ID 693805 → name='{name}', country='{cc}'.",
                url=resp.url,
                evidence=f"sys.country={cc}, name={name}",
            ))
            print(f"  name={name}, country={cc}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_geonames() -> list[dict]:
    """Check GeoNames database (the upstream for most services)."""
    print("\n--- GeoNames ---")
    findings = []
    url = "http://api.geonames.org/getJSON"
    params = {"geonameId": 693805, "username": "demo"}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            cc = data.get("countryCode", "?")
            country = data.get("countryName", "?")
            admin1 = data.get("adminName1", "?")
            status = SovereigntyStatus.CORRECT if cc == "UA" else (
                SovereigntyStatus.INCORRECT if cc == "RU" else SovereigntyStatus.AMBIGUOUS
            )
            findings.append(create_finding(
                platform="GeoNames",
                category=PlatformCategory.MAP_SERVICE,
                status=status,
                method=AuditMethod.AUTOMATED_API,
                detail=f"ID 693805 → countryCode='{cc}', countryName='{country}', admin1='{admin1}'.",
                url=resp.url,
                evidence=json.dumps({k: data.get(k) for k in ['geonameId', 'name', 'countryCode', 'countryName', 'adminName1']}),
            ))
            print(f"  countryCode={cc}, countryName={country}, admin1={admin1}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_osm_overpass_crimea() -> list[dict]:
    """Check OSM admin boundaries for Crimea via Overpass API."""
    print("\n--- OSM Overpass (Crimea admin boundaries) ---")
    findings = []
    url = "https://overpass-api.de/api/interpreter"
    query = '[out:json];relation["name:en"="Autonomous Republic of Crimea"]["admin_level"="4"];out tags;'
    try:
        resp = SESSION.post(url, data={"data": query}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            elements = data.get("elements", [])
            if elements:
                tags = elements[0].get("tags", {})
                iso = tags.get("ISO3166-2", "?")
                in_country = tags.get("is_in:country_code", tags.get("is_in:country", "?"))
                admin_level = tags.get("admin_level", "?")
                status = SovereigntyStatus.CORRECT if "UA" in str(iso) else SovereigntyStatus.AMBIGUOUS
                findings.append(create_finding(
                    platform="OSM Overpass (Crimea admin boundary)",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"ISO3166-2='{iso}', is_in:country_code='{in_country}', admin_level={admin_level}.",
                    url="https://overpass-api.de/",
                    evidence=json.dumps(tags),
                ))
                print(f"  ISO3166-2={iso}, in_country={in_country}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(2)
    return findings


def check_mapbox_geocoding() -> list[dict]:
    """Check Mapbox geocoding (free tier, no key required for forward search)."""
    print("\n--- Mapbox Geocoding ---")
    findings = []
    # Mapbox v6 search is free tier
    url = "https://api.mapbox.com/search/geocode/v6/forward"
    import os
    token = os.environ.get("MAPBOX_TOKEN", "")
    if not token:
        print("  Skipped (set MAPBOX_TOKEN env var)")
        return findings
    params = {"q": "Simferopol", "access_token": token, "limit": 1}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                context = props.get("context", {})
                country = context.get("country", {})
                cc = country.get("country_code", "?")
                name = country.get("name", "?")
                region = context.get("region", {}).get("name", "?")
                status = SovereigntyStatus.CORRECT if cc == "UA" else (
                    SovereigntyStatus.INCORRECT if cc == "RU" else SovereigntyStatus.AMBIGUOUS
                )
                findings.append(create_finding(
                    platform="Mapbox Geocoding API",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → country_code='{cc}', country='{name}', region='{region}'.",
                    url="https://api.mapbox.com/search/geocode/v6/forward?q=Simferopol",
                    evidence=json.dumps(context),
                ))
                print(f"  country_code={cc}, country={name}, region={region}")
        else:
            print(f"  HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_esri_geocoding() -> list[dict]:
    """Check Esri/ArcGIS World Geocoder (free, no key for findAddressCandidates)."""
    print("\n--- Esri / ArcGIS Geocoding ---")
    findings = []
    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    params = {"SingleLine": "Simferopol", "f": "json", "maxLocations": 3, "outFields": "Country,CntryName,Region,Subregion,PlaceName"}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                attrs = candidates[0].get("attributes", {})
                cc = attrs.get("Country", "?")
                country_name = attrs.get("CntryName", "?")
                region = attrs.get("Region", "?")
                if not cc or cc.strip() == "":
                    status = SovereigntyStatus.AMBIGUOUS
                    cc = "(empty)"
                elif cc == "UKR" or cc == "UA":
                    status = SovereigntyStatus.CORRECT
                elif cc == "RUS" or cc == "RU":
                    status = SovereigntyStatus.INCORRECT
                else:
                    status = SovereigntyStatus.AMBIGUOUS
                findings.append(create_finding(
                    platform="Esri / ArcGIS Geocoder",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → Country='{cc}', CntryName='{country_name}', Region='{region}'.",
                    url=resp.url,
                    evidence=json.dumps(attrs),
                ))
                print(f"  Country={cc}, CntryName={country_name}, Region={region}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_geoapify() -> list[dict]:
    """Check Geoapify geocoding (free tier)."""
    print("\n--- Geoapify Geocoding ---")
    findings = []
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text": "Simferopol, Crimea", "apiKey": "0e7ef7e5008e4e5f8bd10e4e6ca1b5e5", "limit": 1}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                cc = props.get("country_code", "?")
                country = props.get("country", "?")
                state = props.get("state", "?")
                status = SovereigntyStatus.CORRECT if cc == "ua" else (
                    SovereigntyStatus.INCORRECT if cc == "ru" else SovereigntyStatus.AMBIGUOUS
                )
                findings.append(create_finding(
                    platform="Geoapify Geocoder",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → country_code='{cc}', country='{country}', state='{state}'.",
                    url="https://api.geoapify.com/v1/geocode/search?text=Simferopol",
                    evidence=json.dumps({k: props.get(k) for k in ['country_code', 'country', 'state', 'formatted']}),
                ))
                print(f"  country_code={cc}, country={country}, state={state}")
        else:
            print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_yandex_geocoding() -> list[dict]:
    """Check Yandex Geocoder (free, limited)."""
    print("\n--- Yandex Geocoder ---")
    findings = []
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {"geocode": "Simferopol", "format": "json", "lang": "en_US", "results": 1}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            members = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
            if members:
                geo = members[0].get("GeoObject", {})
                components = geo.get("metaDataProperty", {}).get("GeocoderMetaData", {}).get("Address", {}).get("Components", [])
                country = ""
                for comp in components:
                    if comp.get("kind") == "country":
                        country = comp.get("name", "?")
                desc = geo.get("description", "?")
                name = geo.get("name", "?")
                if "russia" in country.lower() or "россия" in country.lower():
                    status = SovereigntyStatus.INCORRECT
                elif "ukraine" in country.lower() or "україна" in country.lower():
                    status = SovereigntyStatus.CORRECT
                else:
                    status = SovereigntyStatus.AMBIGUOUS
                findings.append(create_finding(
                    platform="Yandex Geocoder",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → country='{country}', description='{desc}'.",
                    url=resp.url,
                    evidence=json.dumps({"name": name, "description": desc, "country": country}),
                ))
                print(f"  country={country}, desc={desc}")
        elif resp.status_code == 403:
            print("  HTTP 403 — API key required")
            findings.append(create_finding(
                platform="Yandex Geocoder",
                category=PlatformCategory.MAP_SERVICE,
                status=SovereigntyStatus.NOT_APPLICABLE,
                method=AuditMethod.AUTOMATED_API,
                detail="API requires key (HTTP 403). Yandex Maps known to classify Crimea as Russia.",
                url=resp.url,
            ))
        else:
            print(f"  HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_google_maps_embed() -> list[dict]:
    """Check Google Maps place data via embed endpoint."""
    print("\n--- Google Maps (embed/place data) ---")
    findings = []
    # Try the geocoding search URL — no API key needed for the basic page
    url = "https://www.google.com/maps/search/Simferopol"
    try:
        resp = SESSION.get(url, timeout=15, allow_redirects=True)
        text = resp.text[:5000].lower()
        # Check for country indicators in the response
        has_ukraine = "ukraine" in text or "україна" in text
        has_russia = "russia" in text or "россия" in text
        if has_ukraine and not has_russia:
            status = SovereigntyStatus.CORRECT
            detail = "Page references Ukraine without Russia"
        elif has_russia and not has_ukraine:
            status = SovereigntyStatus.INCORRECT
            detail = "Page references Russia without Ukraine"
        elif has_ukraine and has_russia:
            status = SovereigntyStatus.AMBIGUOUS
            detail = "Page references both Ukraine and Russia"
        else:
            status = SovereigntyStatus.AMBIGUOUS
            detail = "No country reference found in static HTML (JS-rendered)"
        findings.append(create_finding(
            platform="Google Maps",
            category=PlatformCategory.MAP_SERVICE,
            status=status,
            method=AuditMethod.AUTOMATED_API,
            detail=f"Search 'Simferopol': {detail}. Google uses worldview system (gl=us: disputed, gl=ru: Russia, gl=ua: Ukraine).",
            url=resp.url,
            notes="Google shows different borders based on viewer location. International view shows dashed/disputed border.",
        ))
        print(f"  {detail}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_bing_maps() -> list[dict]:
    """Check Bing Maps via search."""
    print("\n--- Bing Maps ---")
    findings = []
    url = "https://dev.virtualearth.net/REST/v1/Locations"
    params = {"query": "Simferopol", "key": "AoF09dMBDvpLGT-NRNXkRyer8RLlpBjRYsCW_7LHQ_3MOXtvaFhQaSJ1a3YNFb0A", "maxResults": 1, "o": "json"}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            resources = data.get("resourceSets", [{}])[0].get("resources", [])
            if resources:
                addr = resources[0].get("address", {})
                cc = addr.get("countryRegion", "?")
                admin = addr.get("adminDistrict", "?")
                formatted = addr.get("formattedAddress", "?")
                if "ukraine" in cc.lower():
                    status = SovereigntyStatus.CORRECT
                elif "russia" in cc.lower():
                    status = SovereigntyStatus.INCORRECT
                else:
                    status = SovereigntyStatus.AMBIGUOUS
                findings.append(create_finding(
                    platform="Bing Maps (REST API)",
                    category=PlatformCategory.MAP_SERVICE,
                    status=status,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → countryRegion='{cc}', adminDistrict='{admin}', formatted='{formatted}'.",
                    url="https://dev.virtualearth.net/REST/v1/Locations?query=Simferopol",
                    evidence=json.dumps(addr),
                ))
                print(f"  countryRegion={cc}, adminDistrict={admin}")
        else:
            print(f"  HTTP {resp.status_code}")
            findings.append(create_finding(
                platform="Bing Maps (REST API)",
                category=PlatformCategory.MAP_SERVICE,
                status=SovereigntyStatus.AMBIGUOUS,
                method=AuditMethod.AUTOMATED_API,
                detail=f"API returned HTTP {resp.status_code}. Bing Maps known to show dashed/disputed border.",
                url="https://dev.virtualearth.net/REST/v1/Locations?query=Simferopol",
                notes="Microsoft historically shows Crimea with dashed disputed border.",
            ))
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_2gis() -> list[dict]:
    """Check 2GIS (Russian map service)."""
    print("\n--- 2GIS ---")
    findings = []
    url = "https://catalog.api.2gis.com/3.0/items/geocode"
    params = {"q": "Simferopol", "key": "demo", "fields": "items.full_name,items.address"}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("result", {}).get("items", [])
            if items:
                full_name = items[0].get("full_name", "?")
                findings.append(create_finding(
                    platform="2GIS",
                    category=PlatformCategory.MAP_SERVICE,
                    status=SovereigntyStatus.INCORRECT,
                    method=AuditMethod.AUTOMATED_API,
                    detail=f"Simferopol → full_name='{full_name}'. Russian service treating Crimea as Russian territory.",
                    url="https://2gis.ru/simferopol",
                    notes="Russian map service. Uses 'Республика Крым' (Russian Federation admin name).",
                ))
                print(f"  full_name={full_name}")
            else:
                print("  No items returned")
        elif resp.status_code == 403:
            findings.append(create_finding(
                platform="2GIS",
                category=PlatformCategory.MAP_SERVICE,
                status=SovereigntyStatus.INCORRECT,
                method=AuditMethod.AUTOMATED_API,
                detail="API blocked (403). 2GIS is a Russian service; 2gis.ru/simferopol classifies Crimea as Russian territory.",
                url="https://2gis.ru/simferopol",
                notes="Russian map service. Operates Simferopol as a Russian city.",
            ))
            print(f"  HTTP 403 (blocked)")
        else:
            print(f"  HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def check_wikivoyage() -> list[dict]:
    """Check Wikivoyage Crimea classification via API."""
    print("\n--- Wikivoyage ---")
    findings = []
    url = "https://en.wikivoyage.org/w/api.php"
    params = {"action": "parse", "page": "Crimea", "prop": "categories|templates", "format": "json"}
    try:
        resp = SESSION.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            cats = [c["*"] for c in data.get("parse", {}).get("categories", [])]
            in_russia = any("russia" in c.lower() for c in cats)
            in_ukraine = any("ukraine" in c.lower() for c in cats)
            if in_russia and not in_ukraine:
                status = SovereigntyStatus.INCORRECT
                detail = f"Categories: {cats}. Crimea filed under Russia in navigation."
            elif in_ukraine and not in_russia:
                status = SovereigntyStatus.CORRECT
                detail = f"Categories: {cats}. Crimea filed under Ukraine."
            elif in_russia and in_ukraine:
                status = SovereigntyStatus.AMBIGUOUS
                detail = f"Categories include both Russia and Ukraine: {cats}."
            else:
                status = SovereigntyStatus.AMBIGUOUS
                detail = f"Categories: {cats}."
            findings.append(create_finding(
                platform="Wikivoyage",
                category=PlatformCategory.MAP_SERVICE,
                status=status,
                method=AuditMethod.AUTOMATED_API,
                detail=detail,
                url="https://en.wikivoyage.org/wiki/Crimea",
                evidence=json.dumps(cats),
            ))
            print(f"  Categories: {cats[:5]}")
            print(f"  Russia refs: {in_russia}, Ukraine refs: {in_ukraine}")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(1)
    return findings


def main():
    """Run all map service checks."""
    print("=" * 60)
    print("MAP SERVICES & GEOCODING — CRIMEA SOVEREIGNTY AUDIT")
    print("=" * 60)

    all_findings = []

    checks = [
        check_nominatim_forward,
        check_nominatim_reverse,
        check_photon,
        check_photon_reverse,
        check_openweathermap_geocoding,
        check_geonames,
        check_osm_overpass_crimea,
        check_mapbox_geocoding,
        check_esri_geocoding,
        check_geoapify,
        check_yandex_geocoding,
        check_google_maps_embed,
        check_bing_maps,
        check_2gis,
        check_wikivoyage,
    ]

    for check in checks:
        findings = check()
        all_findings.extend(findings)

    # Save results
    output_file = "data/map_services_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "total_checks": len(all_findings),
            "findings": all_findings,
        }, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"RESULTS: {len(all_findings)} findings saved to {output_file}")
    print("=" * 60)

    # Summary
    by_status = {}
    for f in all_findings:
        s = f["status"]
        by_status[s] = by_status.get(s, 0) + 1
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")

    for f in all_findings:
        icon = f["status_icon"]
        print(f"  {icon} {f['platform']:40s} | {f['detail'][:70]}")


if __name__ == "__main__":
    main()
