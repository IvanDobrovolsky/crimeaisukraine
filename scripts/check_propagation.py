"""
Dependency Propagation Analysis

Quantifies how Natural Earth's Crimea classification cascades through
the open source ecosystem. Collects download counts, dependent counts,
and estimates total exposure.

This provides the "big number" for the research paper.

Usage:
    python scripts/check_propagation.py
"""

import json
import time
from datetime import datetime, timezone

import requests

from audit_framework import (
    AuditDatabase,
    AuditMethod,
    PlatformCategory,
    SovereigntyStatus,
    create_finding,
    DATA_DIR,
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CrimeaSovereigntyAudit/1.0 (research)"})


def get_npm_downloads(package: str) -> dict:
    """Get weekly and monthly download counts from npm."""
    result = {"weekly": 0, "monthly": 0}
    try:
        for period, key in [("last-week", "weekly"), ("last-month", "monthly")]:
            resp = SESSION.get(
                f"https://api.npmjs.org/downloads/point/{period}/{package}",
                timeout=10,
            )
            if resp.status_code == 200:
                result[key] = resp.json().get("downloads", 0)
    except Exception:
        pass
    return result


def get_pypi_downloads(package: str) -> dict:
    """Get recent download counts from PyPI."""
    try:
        resp = SESSION.get(
            f"https://pypistats.org/api/packages/{package}/recent",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()["data"]
            return {
                "weekly": data.get("last_week", 0),
                "monthly": data.get("last_month", 0),
            }
    except Exception:
        pass
    return {"weekly": 0, "monthly": 0}


def get_librariesio_dependents(platform: str, package: str) -> dict:
    """Get dependent counts from libraries.io."""
    try:
        resp = SESSION.get(
            f"https://libraries.io/api/{platform}/{package}",
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "dependent_packages": data.get("dependents_count", 0),
                "dependent_repos": data.get("dependent_repos_count", 0),
                "stars": data.get("stars", 0),
                "source_rank": data.get("rank", 0),
            }
    except Exception:
        pass
    return {}


def analyze_propagation():
    """Build the full propagation analysis."""
    print("=" * 60)
    print("DEPENDENCY PROPAGATION ANALYSIS")
    print("How Natural Earth's Crimea=Russia cascades through open source")
    print("=" * 60)

    # ── NPM ecosystem ────────────────────────────────────────────
    npm_packages = {
        # Tier 1: Direct Natural Earth consumers (contain NE data)
        "world-atlas": {
            "tier": 1,
            "desc": "D3 world-atlas — packages NE as TopoJSON",
            "contains_ne_data": True,
        },
        # Tier 2: Libraries with built-in NE-derived geo data
        "plotly.js": {
            "tier": 2,
            "desc": "Plotly.js — built-in choropleth with NE boundaries",
            "contains_ne_data": True,
        },
        "echarts": {
            "tier": 2,
            "desc": "Apache ECharts — built-in map data",
            "contains_ne_data": True,
        },
        "highcharts": {
            "tier": 2,
            "desc": "Highcharts — map collection (CORRECT for Crimea)",
            "contains_ne_data": True,
        },
        # Tier 3: Libraries that render NE-sourced data
        "d3-geo": {
            "tier": 3,
            "desc": "D3 geo projections — renders NE-sourced maps",
            "contains_ne_data": False,
        },
        "topojson-client": {
            "tier": 3,
            "desc": "TopoJSON decoder — processes NE-based files",
            "contains_ne_data": False,
        },
        "leaflet": {
            "tier": 3,
            "desc": "Leaflet — tile-based, commonly paired with NE",
            "contains_ne_data": False,
        },
        # Tier 4: Downstream wrappers
        "react-simple-maps": {
            "tier": 4,
            "desc": "React wrapper for D3 geo + world-atlas",
            "contains_ne_data": False,
        },
        "vue-echarts": {
            "tier": 4,
            "desc": "Vue wrapper for ECharts",
            "contains_ne_data": False,
        },
        "react-leaflet": {
            "tier": 4,
            "desc": "React wrapper for Leaflet",
            "contains_ne_data": False,
        },
        "angular-highcharts": {
            "tier": 4,
            "desc": "Angular wrapper for Highcharts",
            "contains_ne_data": False,
        },
    }

    npm_results = []
    print("\n--- npm Package Analysis ---")
    for pkg, meta in npm_packages.items():
        downloads = get_npm_downloads(pkg)
        deps = get_librariesio_dependents("npm", pkg)
        result = {
            "package": pkg,
            "ecosystem": "npm",
            **meta,
            **downloads,
            **deps,
        }
        npm_results.append(result)
        print(
            f"  T{meta['tier']} {pkg}: "
            f"{downloads['weekly']:,}/wk, "
            f"{deps.get('dependent_repos', '?')} repos, "
            f"{deps.get('stars', '?')} stars"
        )
        time.sleep(1)

    # ── Python ecosystem ─────────────────────────────────────────
    py_packages = {
        "plotly": {
            "tier": 2,
            "desc": "Plotly Python — uses NE boundaries via plotly.js",
            "contains_ne_data": True,
        },
        "geopandas": {
            "tier": 2,
            "desc": "GeoPandas — default datasets use Natural Earth",
            "contains_ne_data": True,
        },
        "folium": {
            "tier": 3,
            "desc": "Folium — Python Leaflet wrapper, commonly uses NE",
            "contains_ne_data": False,
        },
        "cartopy": {
            "tier": 2,
            "desc": "Cartopy — built-in NE feature download",
            "contains_ne_data": True,
        },
        "pycountry": {
            "tier": 3,
            "desc": "ISO standard wrapper — follows ISO 3166",
            "contains_ne_data": False,
        },
        "pydeck": {
            "tier": 3,
            "desc": "deck.gl Python wrapper — uses Mapbox/NE tiles",
            "contains_ne_data": False,
        },
        "altair": {
            "tier": 3,
            "desc": "Altair — Vega-Lite viz, uses world-atlas TopoJSON",
            "contains_ne_data": False,
        },
    }

    py_results = []
    print("\n--- Python Package Analysis ---")
    for pkg, meta in py_packages.items():
        downloads = get_pypi_downloads(pkg)
        deps = get_librariesio_dependents("pypi", pkg)
        result = {
            "package": pkg,
            "ecosystem": "pypi",
            **meta,
            **downloads,
            **deps,
        }
        py_results.append(result)
        print(
            f"  T{meta['tier']} {pkg}: "
            f"{downloads['monthly']:,}/mo, "
            f"{deps.get('dependent_repos', '?')} repos"
        )
        time.sleep(1)

    # ── Aggregation ──────────────────────────────────────────────
    all_results = npm_results + py_results

    # Total downloads (deduplicated by tier — only count direct NE consumers)
    npm_tier12_weekly = sum(
        r["weekly"] for r in npm_results
        if r["tier"] <= 2 and r["contains_ne_data"]
    )
    npm_all_weekly = sum(r["weekly"] for r in npm_results)
    py_tier12_monthly = sum(
        r["monthly"] for r in py_results
        if r["tier"] <= 2 and r["contains_ne_data"]
    )
    py_all_monthly = sum(r["monthly"] for r in py_results)

    total_dependent_repos = sum(
        r.get("dependent_repos", 0) for r in all_results
    )
    total_dependent_packages = sum(
        r.get("dependent_packages", 0) for r in all_results
    )

    print(f"\n{'='*60}")
    print("PROPAGATION SUMMARY")
    print(f"{'='*60}")
    print(f"\nnpm ecosystem:")
    print(f"  Libraries with NE data (Tier 1-2): {npm_tier12_weekly:,}/week")
    print(f"  All geo libraries: {npm_all_weekly:,}/week")
    print(f"\nPython ecosystem:")
    print(f"  Libraries with NE data (Tier 1-2): {py_tier12_monthly:,}/month")
    print(f"  All geo libraries: {py_all_monthly:,}/month")
    print(f"\nDependent projects:")
    print(f"  Packages depending on these: {total_dependent_packages:,}")
    print(f"  Repositories depending on these: {total_dependent_repos:,}")

    # Save detailed results
    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "npm_packages": npm_results,
        "python_packages": py_results,
        "totals": {
            "npm_tier12_weekly_downloads": npm_tier12_weekly,
            "npm_all_weekly_downloads": npm_all_weekly,
            "python_tier12_monthly_downloads": py_tier12_monthly,
            "python_all_monthly_downloads": py_all_monthly,
            "total_dependent_packages": total_dependent_packages,
            "total_dependent_repos": total_dependent_repos,
        },
    }

    outpath = DATA_DIR / "propagation.json"
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nDetailed results saved to: {outpath}")

    # Add summary finding to audit database
    db = AuditDatabase()
    db.add(create_finding(
        platform="Natural Earth Propagation (aggregate)",
        category=PlatformCategory.OPEN_SOURCE,
        status=SovereigntyStatus.INCORRECT,
        method=AuditMethod.AUTOMATED_API,
        detail=(
            f"Natural Earth's Crimea=Russia propagates to: "
            f"{npm_all_weekly:,} weekly npm downloads, "
            f"{py_all_monthly:,} monthly PyPI downloads, "
            f"{total_dependent_repos:,} dependent repositories, "
            f"{total_dependent_packages:,} dependent packages. "
            f"Only Highcharts (of major libraries) overrides NE to "
            f"correctly assign Crimea to Ukraine."
        ),
        url="https://www.naturalearthdata.com/",
        notes="Aggregate propagation metric across npm + PyPI ecosystems.",
    ))
    db.save()

    return output


if __name__ == "__main__":
    analyze_propagation()
