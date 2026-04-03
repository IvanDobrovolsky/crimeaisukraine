"""
Reference template generation for CrimeaLens.

Generates binary contour masks from geographic data (GeoJSON/Natural Earth)
for Ukraine-with-Crimea, Russia-with-Crimea, and Crimea standalone.
These templates are used as ground truth for shape matching.
"""

import json
import urllib.request
from pathlib import Path

import cv2
import numpy as np

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# Crimea bounding box (approx) in geographic coordinates
CRIMEA_BBOX = {
    "min_lon": 32.4,
    "max_lon": 36.7,
    "min_lat": 44.3,
    "max_lat": 46.3,
}

# Canvas size for rendered templates
TEMPLATE_SIZE = 512

# GeoJSON sources — Natural Earth simplified boundaries
GEOJSON_URLS = {
    "countries_50m": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
}


def download_geojson(url: str, cache_dir: Path | None = None) -> dict:
    """Download and cache a GeoJSON file."""
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / url.split("/")[-1]
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)

    print(f"  Downloading {url.split('/')[-1]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "CrimeaLens/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())

    if cache_dir:
        with open(cache_file, "w") as f:
            json.dump(data, f)

    return data


def extract_country_polygons(geojson: dict, iso_a2: str) -> list[np.ndarray]:
    """Extract all polygon coordinate arrays for a country by ISO A2 code."""
    polygons = []
    for feature in geojson["features"]:
        props = feature.get("properties", {})
        code = props.get("ISO_A2") or props.get("iso_a2") or props.get("ISO_A2_EH", "")
        if code != iso_a2:
            continue

        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            polygons.append(np.array(geom["coordinates"][0]))
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                polygons.append(np.array(poly[0]))
    return polygons


def geo_to_pixel(coords: np.ndarray, bbox: dict, size: int) -> np.ndarray:
    """Convert geographic coordinates to pixel coordinates within a bounding box."""
    lon = coords[:, 0]
    lat = coords[:, 1]

    x = (lon - bbox["min_lon"]) / (bbox["max_lon"] - bbox["min_lon"]) * (size - 1)
    y = (bbox["max_lat"] - lat) / (bbox["max_lat"] - bbox["min_lat"]) * (size - 1)

    return np.column_stack([x, y]).astype(np.int32)


def polygon_intersects_bbox(coords: np.ndarray, bbox: dict) -> bool:
    """Check if a polygon's bounding box overlaps with the target bbox."""
    lons = coords[:, 0]
    lats = coords[:, 1]
    return not (
        lons.max() < bbox["min_lon"]
        or lons.min() > bbox["max_lon"]
        or lats.max() < bbox["min_lat"]
        or lats.min() > bbox["max_lat"]
    )


def render_mask(
    polygons: list[np.ndarray], bbox: dict, size: int = TEMPLATE_SIZE
) -> np.ndarray:
    """Render polygons as a filled binary mask."""
    mask = np.zeros((size, size), dtype=np.uint8)
    for coords in polygons:
        if polygon_intersects_bbox(coords, bbox):
            pixels = geo_to_pixel(coords, bbox, size)
            cv2.fillPoly(mask, [pixels], 255)
    return mask


def extract_crimea_contour(mask: np.ndarray) -> np.ndarray | None:
    """Extract the largest contour from a Crimea-region mask (the peninsula itself)."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    # Crimea peninsula is the largest contour in the Crimea bbox region
    return max(contours, key=cv2.contourArea)


def compute_hu_moments(contour: np.ndarray) -> np.ndarray:
    """Compute Hu moments for a contour (7 values, scale/rotation invariant)."""
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()
    # Log-transform for numerical stability (Hu moments span many orders of magnitude)
    hu_log = -np.sign(hu) * np.log10(np.abs(hu) + 1e-30)
    return hu_log


def generate_templates(cache_dir: Path | None = None) -> dict[str, dict]:
    """
    Generate all reference templates from geographic data.

    Returns dict with keys: 'crimea', 'ukraine_with_crimea', 'russia_with_crimea'
    Each value has: 'mask', 'contour', 'hu_moments'
    """
    print("Generating CrimeaLens reference templates...")

    geojson = download_geojson(GEOJSON_URLS["countries_50m"], cache_dir)

    ua_polys = extract_country_polygons(geojson, "UA")
    ru_polys = extract_country_polygons(geojson, "RU")

    print(f"  Ukraine: {len(ua_polys)} polygons, Russia: {len(ru_polys)} polygons")

    # Render masks focused on Crimea region
    ua_mask = render_mask(ua_polys, CRIMEA_BBOX, TEMPLATE_SIZE)
    ru_mask = render_mask(ru_polys, CRIMEA_BBOX, TEMPLATE_SIZE)

    # Extract Crimea contour from each — whichever country "has" Crimea
    # in Natural Earth (Russia by default at 50m), that mask will have the peninsula
    ua_crimea_contour = extract_crimea_contour(ua_mask)
    ru_crimea_contour = extract_crimea_contour(ru_mask)

    # The standalone Crimea contour — from whichever has it
    if ru_crimea_contour is not None and cv2.contourArea(ru_crimea_contour) > 100:
        crimea_contour = ru_crimea_contour
        crimea_source = "russia"
    elif ua_crimea_contour is not None and cv2.contourArea(ua_crimea_contour) > 100:
        crimea_contour = ua_crimea_contour
        crimea_source = "ukraine"
    else:
        raise RuntimeError("Could not extract Crimea contour from either country")

    print(f"  Crimea contour extracted from {crimea_source} polygon")
    print(f"  Crimea contour area: {cv2.contourArea(crimea_contour):.0f} px")

    # Compute Hu moments for the Crimea peninsula shape
    crimea_hu = compute_hu_moments(crimea_contour)

    # Now render broader context masks (for the full Ukraine/Russia shapes
    # to help with country identification in input images)
    broad_bbox = {
        "min_lon": 22.0,
        "max_lon": 45.0,
        "min_lat": 42.0,
        "max_lat": 53.0,
    }
    ua_broad_mask = render_mask(ua_polys, broad_bbox, TEMPLATE_SIZE)
    ru_broad_mask = render_mask(ru_polys, broad_bbox, TEMPLATE_SIZE)

    ua_contours, _ = cv2.findContours(ua_broad_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ru_contours, _ = cv2.findContours(ru_broad_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ua_main = max(ua_contours, key=cv2.contourArea) if ua_contours else None
    ru_main = max(ru_contours, key=cv2.contourArea) if ru_contours else None

    templates = {
        "crimea": {
            "contour": crimea_contour,
            "hu_moments": crimea_hu,
            "mask": render_mask(
                [coords for coords in (ua_polys + ru_polys) if polygon_intersects_bbox(coords, CRIMEA_BBOX)],
                CRIMEA_BBOX,
                TEMPLATE_SIZE,
            ),
            "source": crimea_source,
        },
        "ukraine": {
            "contour": ua_main,
            "hu_moments": compute_hu_moments(ua_main) if ua_main is not None else None,
            "mask": ua_broad_mask,
            "crimea_mask": ua_mask,
        },
        "russia": {
            "contour": ru_main,
            "hu_moments": compute_hu_moments(ru_main) if ru_main is not None else None,
            "mask": ru_broad_mask,
            "crimea_mask": ru_mask,
        },
    }

    print(f"  Ukraine Crimea-region coverage: {np.count_nonzero(ua_mask)} px")
    print(f"  Russia Crimea-region coverage: {np.count_nonzero(ru_mask)} px")
    print("  Templates generated successfully.")

    return templates


def save_templates(templates: dict, output_dir: Path | None = None) -> Path:
    """Save templates to .npz files."""
    out = output_dir or TEMPLATES_DIR
    out.mkdir(parents=True, exist_ok=True)

    for name, data in templates.items():
        path = out / f"{name}.npz"
        save_data = {}
        if data.get("contour") is not None:
            save_data["contour"] = data["contour"]
        if data.get("hu_moments") is not None:
            save_data["hu_moments"] = data["hu_moments"]
        if data.get("mask") is not None:
            save_data["mask"] = data["mask"]
        if data.get("crimea_mask") is not None:
            save_data["crimea_mask"] = data["crimea_mask"]
        np.savez_compressed(path, **save_data)

    print(f"  Saved templates to {out}/")
    return out


def load_templates(templates_dir: Path | None = None) -> dict[str, dict]:
    """Load pre-computed templates from .npz files."""
    src = templates_dir or TEMPLATES_DIR
    templates = {}
    for name in ["crimea", "ukraine", "russia"]:
        path = src / f"{name}.npz"
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}. Run `crimealens --generate-templates` first.")
        data = np.load(path, allow_pickle=False)
        templates[name] = {k: data[k] for k in data.files}
    return templates


if __name__ == "__main__":
    cache = TEMPLATES_DIR / ".cache"
    templates = generate_templates(cache_dir=cache)
    save_templates(templates)
