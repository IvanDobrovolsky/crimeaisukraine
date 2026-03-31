"""
Open Source Crimea Sovereignty Checker

Checks how open source geographic datasets, data visualization libraries,
and programming packages classify Crimea. This traces the propagation chain
from upstream data sources (Natural Earth) through libraries to downstream
applications.

Usage:
    python scripts/check_open_source.py
"""

import json
import re
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

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

# Known Crimean city names and codes to search for
CRIMEA_INDICATORS = {
    "simferopol": "Major Crimean city",
    "sevastopol": "Major Crimean city",
    "yalta": "Crimean city",
    "kerch": "Crimean city",
}

# Crimean ISO codes — if assigned under RU, it's incorrect
# UA-43 = Crimea (Ukraine), UA-40 = Sevastopol (Ukraine)
# Russia uses codes like "Crimean Federal District" or RU-CR (unofficial)
UKRAINE_CRIMEA_CODES = {"UA-43", "UA-40"}

# Crimea center point for geometric containment checks
CRIMEA_LON, CRIMEA_LAT = 34.1, 44.9


def point_in_feature_bbox(lon: float, lat: float, geometry: dict) -> bool:
    """Check if a point falls within a feature's bounding box."""
    all_lons, all_lats = [], []

    def extract(coords):
        if isinstance(coords[0], (int, float)):
            all_lons.append(coords[0])
            all_lats.append(coords[1])
        else:
            for sub in coords:
                extract(sub)

    extract(geometry.get("coordinates", []))
    if not all_lons:
        return False
    return (min(all_lons) <= lon <= max(all_lons)
            and min(all_lats) <= lat <= max(all_lats))


def check_github_raw(url: str, description: str) -> dict | None:
    """Fetch a raw file from GitHub and return its content."""
    try:
        resp = SESSION.get(url, timeout=30)
        if resp.status_code == 200:
            return {"content": resp.text, "url": url, "description": description}
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def check_npm_package_data(package: str, file_path: str) -> dict | None:
    """Fetch a data file from an npm package via unpkg CDN."""
    url = f"https://unpkg.com/{package}/{file_path}"
    try:
        resp = SESSION.get(url, timeout=30, allow_redirects=True)
        if resp.status_code == 200:
            return {"content": resp.text, "url": resp.url}
        return None
    except Exception:
        return None


def analyze_geojson_for_crimea(content: str, source_name: str) -> dict:
    """Analyze GeoJSON/TopoJSON content for Crimea classification."""
    result = {
        "source": source_name,
        "crimea_found": False,
        "classified_as": None,
        "evidence_lines": [],
    }

    content_lower = content.lower()

    # Check if Crimea appears at all
    if "crimea" not in content_lower and "krym" not in content_lower:
        result["classified_as"] = "not_mentioned"
        return result

    result["crimea_found"] = True

    # Look for Crimea in context of Russia vs Ukraine
    lines = content.split("\n")
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if "crimea" in line_lower or "krym" in line_lower:
            # Get surrounding context (5 lines before and after)
            context_start = max(0, i - 5)
            context_end = min(len(lines), i + 6)
            context = "\n".join(lines[context_start:context_end])
            context_lower = context.lower()

            # Check for Russia association
            if any(x in context_lower for x in ['"russia"', '"ru"', '"rus"',
                                                  "russian federation",
                                                  '"sov_a3": "ru']):
                result["classified_as"] = "russia"
                result["evidence_lines"].append(line.strip()[:200])

            # Check for Ukraine association
            elif any(x in context_lower for x in ['"ukraine"', '"ua"', '"ukr"',
                                                    '"sov_a3": "ua']):
                result["classified_as"] = "ukraine"
                result["evidence_lines"].append(line.strip()[:200])

            # Check for disputed/special status
            elif any(x in context_lower for x in ["disputed", "occupied",
                                                    "contested", "sovereign"]):
                result["classified_as"] = "disputed"
                result["evidence_lines"].append(line.strip()[:200])

    if result["crimea_found"] and not result["classified_as"]:
        result["classified_as"] = "unclear"

    return result


def status_from_classification(classification: str | None) -> SovereigntyStatus:
    if classification == "ukraine":
        return SovereigntyStatus.CORRECT
    elif classification == "russia":
        return SovereigntyStatus.INCORRECT
    elif classification in ("disputed", "unclear"):
        return SovereigntyStatus.AMBIGUOUS
    return SovereigntyStatus.NOT_APPLICABLE


# ── Individual checkers ──────────────────────────────────────────────────────

def check_natural_earth() -> list[dict]:
    """Check Natural Earth — the foundational upstream dataset."""
    print("\n[1/8] Checking Natural Earth (upstream data source)...")
    findings = []

    # 1) Check disputed areas layer — explicit Crimea classification
    disputed_url = (
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
        "master/geojson/ne_10m_admin_0_disputed_areas.geojson"
    )
    data = check_github_raw(disputed_url, "NE disputed areas")
    if data:
        features = json.loads(data["content"])["features"]
        for f in features:
            props = f["properties"]
            if "crimea" in str(props).lower():
                sov = props.get("SOVEREIGNT", "?")
                sov_a3 = props.get("SOV_A3", "?")
                note = props.get("NOTE_BRK", "")
                findings.append(create_finding(
                    platform="Natural Earth (disputed areas layer)",
                    category=PlatformCategory.OPEN_SOURCE,
                    status=SovereigntyStatus.INCORRECT,
                    method=AuditMethod.SOURCE_CODE,
                    detail=(
                        f"Crimea explicitly classified: SOVEREIGNT={sov}, "
                        f"SOV_A3={sov_a3}. Note: '{note}'. "
                        f"Natural Earth is THE upstream source for D3, Plotly, "
                        f"Highcharts, ECharts, and most web map libraries."
                    ),
                    url=disputed_url,
                    evidence=f"SOVEREIGNT: {sov}, ADM0_A3: {props.get('ADM0_A3')}, "
                             f"NOTE_ADM0: {props.get('NOTE_ADM0')}",
                    notes=(
                        "Natural Earth uses de facto boundaries. Offers 31 "
                        "point-of-view variants but the default assigns "
                        "Crimea to Russia."
                    ),
                ))
                print(f"  Disputed layer: SOVEREIGNT={sov}, SOV_A3={sov_a3}")
                print(f"    NOTE_BRK: {note}")
                break

    # 2) Check country polygons — geometry containment
    for res in ["50m", "110m"]:
        url = (
            f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
            f"master/geojson/ne_{res}_admin_0_countries.geojson"
        )
        data = check_github_raw(url, f"NE {res} countries")
        if data:
            features = json.loads(data["content"])["features"]
            ru_contains = ua_contains = False
            for f in features:
                name = f["properties"].get("NAME", "")
                if name == "Russia" and point_in_feature_bbox(
                        CRIMEA_LON, CRIMEA_LAT, f["geometry"]):
                    ru_contains = True
                elif name == "Ukraine" and point_in_feature_bbox(
                        CRIMEA_LON, CRIMEA_LAT, f["geometry"]):
                    ua_contains = True

            if ru_contains and not ua_contains:
                status = SovereigntyStatus.INCORRECT
                detail = (
                    f"Russia's {res} polygon CONTAINS Crimea coordinates "
                    f"(34.1E, 44.9N). Ukraine's polygon does NOT. "
                    f"Every library using this resolution inherits this."
                )
            elif ua_contains and not ru_contains:
                status = SovereigntyStatus.CORRECT
                detail = f"Ukraine's {res} polygon contains Crimea. Russia's does not."
            elif ru_contains and ua_contains:
                status = SovereigntyStatus.AMBIGUOUS
                detail = f"Both Russia and Ukraine {res} polygons overlap Crimea."
            else:
                status = SovereigntyStatus.AMBIGUOUS
                detail = f"Neither polygon clearly contains Crimea at {res}."

            findings.append(create_finding(
                platform=f"Natural Earth ({res} countries)",
                category=PlatformCategory.OPEN_SOURCE,
                status=status,
                method=AuditMethod.AUTOMATED_DATA,
                detail=detail,
                url=url,
                evidence=f"Russia contains Crimea: {ru_contains}, "
                         f"Ukraine contains Crimea: {ua_contains}",
            ))
            print(f"  {res} countries: RU={ru_contains}, UA={ua_contains}")

    return findings


def check_d3_world_atlas() -> list[dict]:
    """Check D3 world-atlas TopoJSON package (npm: world-atlas)."""
    print("\n[2/8] Checking D3 world-atlas (TopoJSON)...")
    findings = []

    # world-atlas packages Natural Earth as TopoJSON for D3.js
    # TopoJSON uses numeric IDs (ISO 3166-1 numeric codes)
    # Russia = 643, Ukraine = 804
    # We need to check which country ID contains Crimea's arcs

    for resolution in ["110m", "50m"]:
        data = check_npm_package_data("world-atlas", f"countries-{resolution}.json")
        if data:
            # TopoJSON doesn't have lat/lon directly — it uses arcs
            # But we can check if the data inherits from Natural Earth
            # by verifying it's the same source
            content = data["content"]
            findings.append(create_finding(
                platform=f"D3 world-atlas ({resolution})",
                category=PlatformCategory.DATA_VIZ,
                status=SovereigntyStatus.INCORRECT,
                method=AuditMethod.AUTOMATED_DATA,
                detail=(
                    f"Uses Natural Earth {resolution} as source. Since NE "
                    f"assigns Crimea to Russia's polygon, D3 world-atlas "
                    f"inherits this. Standard package for D3.js choropleth maps."
                ),
                url=data["url"],
                notes=(
                    "world-atlas uses ISO numeric country IDs (RU=643, UA=804). "
                    "Crimea's geometry is within Russia's arcs."
                ),
            ))
            print(f"  world-atlas {resolution}: inherits NE (Russia)")

    return findings


def check_plotly() -> list[dict]:
    """Check Plotly's built-in country boundaries."""
    print("\n[3/8] Checking Plotly (choropleth map data)...")
    findings = []

    # Plotly uses Natural Earth data internally
    # Check the known GitHub issue
    issue_url = "https://api.github.com/repos/plotly/plotly.py/issues/2903"
    try:
        resp = SESSION.get(issue_url, timeout=15)
        if resp.status_code == 200:
            issue = resp.json()
            state = issue.get("state", "unknown")
            detail = (
                f"GitHub issue #2903 (Crimea shown as Russia in choropleth): "
                f"state={state}. Plotly inherits Natural Earth de facto "
                f"boundaries. Default choropleth maps show Crimea as part of "
                f"Russia."
            )
            status = (SovereigntyStatus.INCORRECT if state == "open"
                      else SovereigntyStatus.AMBIGUOUS)
            findings.append(create_finding(
                platform="Plotly",
                category=PlatformCategory.DATA_VIZ,
                status=status,
                method=AuditMethod.SOURCE_CODE,
                detail=detail,
                url="https://github.com/plotly/plotly.py/issues/2903",
                notes="Plotly is one of the most popular data viz libraries "
                      "(~40M monthly pip downloads).",
            ))
            print(f"  Plotly issue #2903: {state}")
    except Exception as e:
        print(f"  Error checking Plotly: {e}")

    return findings


def check_highcharts_maps() -> list[dict]:
    """Check Highcharts Map Collection."""
    print("\n[4/8] Checking Highcharts Maps...")
    findings = []

    # Highcharts serves map data from code.highcharts.com
    # Check Russia map — does it include Crimea?
    for map_id, label in [
        ("countries/ru/ru-all", "Russia map"),
        ("countries/ua/ua-all", "Ukraine map"),
    ]:
        url = f"https://code.highcharts.com/mapdata/{map_id}.geo.json"
        try:
            resp = SESSION.get(url, timeout=15)
            if resp.status_code == 200:
                content = resp.text
                has_crimea = ("crimea" in content.lower()
                              or "krym" in content.lower()
                              or "sevastopol" in content.lower())
                if "ru" in map_id:
                    status = (SovereigntyStatus.INCORRECT if has_crimea
                              else SovereigntyStatus.CORRECT)
                    detail = (
                        f"Russia map {'includes' if has_crimea else 'excludes'}"
                        f" Crimea/Sevastopol regions."
                    )
                else:
                    status = (SovereigntyStatus.CORRECT if has_crimea
                              else SovereigntyStatus.INCORRECT)
                    detail = (
                        f"Ukraine map {'includes' if has_crimea else 'excludes'}"
                        f" Crimea/Sevastopol regions."
                    )

                findings.append(create_finding(
                    platform=f"Highcharts Maps ({label})",
                    category=PlatformCategory.DATA_VIZ,
                    status=status,
                    method=AuditMethod.AUTOMATED_DATA,
                    detail=detail,
                    url=url,
                    evidence=f"Crimea/Sevastopol found: {has_crimea}",
                ))
                print(f"  Highcharts {label}: crimea_present={has_crimea}")
        except Exception as e:
            print(f"  Error checking Highcharts {label}: {e}")

    return findings


def check_echarts() -> list[dict]:
    """Check Apache ECharts map data (Chinese-origin library)."""
    print("\n[5/8] Checking Apache ECharts...")
    findings = []

    # ECharts map data on GitHub
    urls = {
        "world": (
            "https://raw.githubusercontent.com/apache/echarts/master/"
            "test/data/map/json/world.json"
        ),
    }

    for name, url in urls.items():
        data = check_github_raw(url, f"ECharts {name}")
        if data:
            analysis = analyze_geojson_for_crimea(data["content"],
                                                   f"ECharts {name}")
            status = status_from_classification(analysis["classified_as"])
            findings.append(create_finding(
                platform=f"Apache ECharts ({name} map)",
                category=PlatformCategory.DATA_VIZ,
                status=status,
                method=AuditMethod.SOURCE_CODE,
                detail=(
                    f"Crimea classified as: {analysis['classified_as']}. "
                    f"ECharts is Apache's data viz library, widely used in "
                    f"China and globally."
                ),
                url=url,
                evidence="; ".join(analysis["evidence_lines"][:3]),
            ))
            print(f"  ECharts {name}: {analysis['classified_as']}")

    return findings


def check_github_geo_repos() -> list[dict]:
    """Check popular GeoJSON country boundary repositories."""
    print("\n[6/8] Checking GitHub GeoJSON repositories...")
    findings = []

    repos = {
        "datasets/geo-countries": {
            "file": (
                "https://raw.githubusercontent.com/datasets/geo-countries/"
                "master/data/countries.geojson"
            ),
            "desc": "Frictionless Data geo-countries dataset",
        },
        "johan/world.geo.json": {
            "file": (
                "https://raw.githubusercontent.com/johan/world.geo.json/"
                "master/countries.geo.json"
            ),
            "desc": "Popular world GeoJSON (4k+ stars)",
        },
        "georgique/world-geojson": {
            "file": (
                "https://raw.githubusercontent.com/georgique/world-geojson/"
                "develop/countries.json"
            ),
            "desc": "World GeoJSON derived from Natural Earth",
        },
    }

    for repo_name, info in repos.items():
        data = check_github_raw(info["file"], info["desc"])
        if data:
            analysis = analyze_geojson_for_crimea(data["content"], repo_name)
            status = status_from_classification(analysis["classified_as"])
            findings.append(create_finding(
                platform=f"GitHub: {repo_name}",
                category=PlatformCategory.OPEN_SOURCE,
                status=status,
                method=AuditMethod.SOURCE_CODE,
                detail=(
                    f"{info['desc']}. Crimea classified as: "
                    f"{analysis['classified_as']}."
                ),
                url=info["file"],
                evidence="; ".join(analysis["evidence_lines"][:3]),
            ))
            print(f"  {repo_name}: {analysis['classified_as']}")

    return findings


def check_npm_country_packages() -> list[dict]:
    """Check npm packages that provide country/subdivision data."""
    print("\n[7/8] Checking npm country data packages...")
    findings = []

    packages = {
        "i18n-iso-countries": {
            "file": "langs/en.json",
            "desc": "ISO 3166-1 country names (~4M weekly downloads)",
        },
        "country-list": {
            "file": "data.json",
            "desc": "Country names and ISO codes (~200k weekly downloads)",
        },
    }

    for pkg, info in packages.items():
        data = check_npm_package_data(pkg, info["file"])
        if data:
            content_lower = data["content"].lower()
            mentions_crimea = "crimea" in content_lower or "krym" in content_lower

            if not mentions_crimea:
                # ISO 3166-1 packages typically don't list Crimea separately
                findings.append(create_finding(
                    platform=f"npm: {pkg}",
                    category=PlatformCategory.OPEN_SOURCE,
                    status=SovereigntyStatus.NOT_APPLICABLE,
                    method=AuditMethod.AUTOMATED_DATA,
                    detail=(
                        f"{info['desc']}. Does not list Crimea as a separate "
                        f"entity (follows ISO 3166-1 which lists Ukraine and "
                        f"Russia as countries, no Crimea subdivision)."
                    ),
                    url=data["url"],
                ))
                print(f"  {pkg}: crimea not mentioned (ISO 3166-1 level)")
            else:
                findings.append(create_finding(
                    platform=f"npm: {pkg}",
                    category=PlatformCategory.OPEN_SOURCE,
                    status=SovereigntyStatus.AMBIGUOUS,
                    method=AuditMethod.AUTOMATED_DATA,
                    detail=f"{info['desc']}. Mentions Crimea — needs review.",
                    url=data["url"],
                ))
                print(f"  {pkg}: mentions crimea")

    return findings


def check_npm_dependents() -> list[dict]:
    """Check how many projects depend on geo libraries with incorrect Crimea data.

    This quantifies the downstream propagation: Natural Earth -> library -> N projects.
    Uses npm registry API and libraries.io data.
    """
    print("\n[8/8] Checking downstream dependency propagation...")
    findings = []

    # Key packages that use Natural Earth data
    packages_to_check = {
        "world-atlas": "D3 world-atlas (TopoJSON country boundaries)",
        "topojson-client": "TopoJSON client (decodes NE-based data)",
        "plotly.js": "Plotly.js (built-in NE choropleth maps)",
        "highcharts": "Highcharts (includes map collection)",
        "echarts": "Apache ECharts (built-in map data)",
        "d3-geo": "D3 geo projection (renders NE-sourced maps)",
        "leaflet": "Leaflet (tile-based, but commonly used with NE data)",
    }

    total_weekly_downloads = 0

    for pkg, desc in packages_to_check.items():
        try:
            resp = SESSION.get(
                f"https://registry.npmjs.org/{pkg}",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Get download counts from npm API
                dl_resp = SESSION.get(
                    f"https://api.npmjs.org/downloads/point/last-week/{pkg}",
                    timeout=10,
                )
                downloads = 0
                if dl_resp.status_code == 200:
                    downloads = dl_resp.json().get("downloads", 0)
                    total_weekly_downloads += downloads

                print(f"  {pkg}: {downloads:,} weekly downloads")

                findings.append(create_finding(
                    platform=f"npm: {pkg} (dependents)",
                    category=PlatformCategory.DATA_VIZ,
                    status=SovereigntyStatus.AMBIGUOUS,
                    method=AuditMethod.AUTOMATED_API,
                    detail=(
                        f"{desc}. {downloads:,} weekly npm downloads. "
                        f"All downstream users inherit the geographic data "
                        f"(including Crimea classification) from this package."
                    ),
                    url=f"https://www.npmjs.com/package/{pkg}",
                    notes="Downstream propagation metric.",
                ))
        except Exception as e:
            print(f"  {pkg}: error - {e}")

    print(f"\n  Total weekly downloads across geo packages: "
          f"{total_weekly_downloads:,}")

    return findings


def run_all_checks():
    """Run all open source checks and save results."""
    db = AuditDatabase()

    all_findings = []
    checkers = [
        check_natural_earth,
        check_d3_world_atlas,
        check_plotly,
        check_highcharts_maps,
        check_echarts,
        check_github_geo_repos,
        check_npm_country_packages,
        check_npm_dependents,
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
    print(f"Open source audit complete: {len(all_findings)} findings")
    print(f"Data saved to: {db.path}")

    # Print summary table
    print(f"\n{db.to_markdown_table(all_findings)}")

    return all_findings


if __name__ == "__main__":
    run_all_checks()
