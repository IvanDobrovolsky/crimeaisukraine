#!/usr/bin/env python3
"""
Fix Crimea sovereignty in Natural Earth ne_10m_admin_0_countries_iso TopoJSON.

Problem: Natural Earth assigns SOVEREIGNT="Russia" to Crimea and Sevastopol,
so the admin-0 countries file draws Crimea inside Russia's polygon.

Fix: Download the admin-1 shapefile, extract the Crimea + Sevastopol polygons,
subtract them from Russia, and union them into Ukraine.

This script patches the exact TopoJSON file used on anthropic.com/features/81k-interviews:
  cdn.sanity.io/files/4zrzovbb/website/cca8d23a9104ef0fc87b518ec18565aa8af41205.json

Usage:
  pip install shapely requests topojson
  python fix_crimea_topojson.py

Output:
  ne_10m_countries_crimea_fixed.json  (drop-in replacement)
"""

import json, sys, urllib.request
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import topojson as tp

ADMIN0_URL = "https://cdn.sanity.io/files/4zrzovbb/website/cca8d23a9104ef0fc87b518ec18565aa8af41205.json"
# Natural Earth admin-1 GeoJSON (has separate Crimea/Sevastopol records with iso_3166_2=UA-43/UA-40)
ADMIN1_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"

OUT = "ne_10m_countries_crimea_fixed.json"


def fetch_json(url: str, label: str) -> dict:
    print(f"Fetching {label}...")
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())


def topojson_to_geojson(topo: dict) -> list:
    """Convert TopoJSON to list of GeoJSON features using topojson library."""
    obj_name = list(topo["objects"].keys())[0]
    fc = tp.Topology(topo).to_geojson()
    return json.loads(fc)["features"]


def extract_crimea_polygons(admin1_geojson: dict):
    """Extract Crimea + Sevastopol polygons from admin-1 data."""
    crimea_parts = []
    for f in admin1_geojson["features"]:
        props = f.get("properties", {})
        iso2 = props.get("iso_3166_2", "")
        adm0 = props.get("adm0_a3", "")
        name = props.get("name", "")
        # UA-43 = Crimea, UA-40 = Sevastopol
        # Also catch Natural Earth's Russia-assigned versions
        if iso2 in ("UA-43", "UA-40") or (
            "crimea" in name.lower() or "sevastopol" in name.lower()
        ):
            geom = shape(f["geometry"])
            if geom.is_valid:
                crimea_parts.append(geom)
                print(f"  Found: {name} (iso_3166_2={iso2}, adm0_a3={adm0})")
    if not crimea_parts:
        sys.exit("ERROR: No Crimea/Sevastopol polygons found in admin-1 data")
    return unary_union(crimea_parts)


def main():
    # 1. Fetch the data
    topo_data = fetch_json(ADMIN0_URL, "admin-0 TopoJSON (Anthropic)")
    admin1_data = fetch_json(ADMIN1_URL, "admin-1 GeoJSON (Natural Earth)")

    # 2. Convert TopoJSON to GeoJSON features
    print("Converting TopoJSON to GeoJSON...")
    features = topojson_to_geojson(topo_data)
    print(f"  {len(features)} country features")

    # 3. Extract Crimea polygon from admin-1
    crimea = extract_crimea_polygons(admin1_data)
    print(f"  Crimea union area: {crimea.area:.4f}")

    # 4. Patch: subtract Crimea from Russia, add to Ukraine
    patched = []
    for f in features:
        name = f["properties"].get("NAME", "")
        geom = shape(f["geometry"])

        if name == "Russia":
            new_geom = geom.difference(crimea)
            print(f"  Russia: subtracted Crimea ({geom.area:.4f} -> {new_geom.area:.4f})")
            f["geometry"] = mapping(new_geom)

        elif name == "Ukraine":
            new_geom = unary_union([geom, crimea])
            print(f"  Ukraine: added Crimea ({geom.area:.4f} -> {new_geom.area:.4f})")
            f["geometry"] = mapping(new_geom)

        patched.append(f)

    # 5. Convert back to TopoJSON
    print("Converting back to TopoJSON...")
    fc = {"type": "FeatureCollection", "features": patched}
    topology = tp.Topology(fc, object_name="ne_10m_admin_0_countries_iso")
    result = topology.to_dict()

    with open(OUT, "w") as fp:
        json.dump(result, fp, separators=(",", ":"))

    size_kb = len(json.dumps(result, separators=(",", ":"))) / 1024
    print(f"\nDone: {OUT} ({size_kb:.0f} KB)")
    print(f"Drop-in replacement — same object name, same property schema.")

    # 6. Verify
    verify_features = topojson_to_geojson(result)
    for f in verify_features:
        name = f["properties"].get("NAME", "")
        if name in ("Russia", "Ukraine"):
            geom = shape(f["geometry"])
            # Point-in-polygon for Simferopol
            from shapely.geometry import Point
            simf = Point(34.10, 44.95)
            contains = geom.contains(simf)
            print(f"  {name} contains Simferopol: {contains}")


if __name__ == "__main__":
    main()
